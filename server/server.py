"""
游戏存档助手 - 网络同步服务器
运行此文件提供配置同步服务
"""

from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# 配置
DATA_DIR = "server_data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
VERSION_FILE = os.path.join(DATA_DIR, "version.txt")
DEVICES_FILE = os.path.join(DATA_DIR, "devices.json")

# 从环境变量读取管理密码，默认为 admin123
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

def ensure_data_dir():
    """确保数据目录存在"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_config():
    """加载配置"""
    ensure_data_dir()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    """保存配置"""
    ensure_data_dir()
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def load_version():
    """加载版本号"""
    ensure_data_dir()
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            try:
                return int(f.read().strip())
            except:
                return 0
    return 0

def save_version(version):
    """保存版本号"""
    ensure_data_dir()
    with open(VERSION_FILE, 'w') as f:
        f.write(str(version))

def load_devices():
    """加载设备列表"""
    ensure_data_dir()
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_devices(devices):
    """保存设备列表"""
    ensure_data_dir()
    with open(DEVICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(devices, f, indent=4, ensure_ascii=False)

def update_device_log(machine_id):
    """更新设备同步日志"""
    devices = load_devices()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    version = load_version()

    # 查找是否已存在该设备
    found = False
    for device in devices:
        if device.get("machine_id") == machine_id:
            device["last_sync"] = now
            device["last_version"] = version
            device["sync_count"] = device.get("sync_count", 0) + 1
            found = True
            break

    if not found:
        devices.append({
            "machine_id": machine_id,
            "first_seen": now,
            "last_sync": now,
            "last_version": version,
            "sync_count": 1
        })

    save_devices(devices)

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "message": "游戏存档同步服务器运行正常"
    })

@app.route('/api/config/sync/<user_id>', methods=['POST'])
def sync_config(user_id):
    """
    同步配置（客户端拉取）

    请求体:
    {
        "local_version": 123,
        "machine_id": "abc123"
    }

    响应:
    {
        "updated": true,
        "config": {...},
        "version": 124
    }
    或
    {
        "updated": false
    }
    """
    data = request.json or {}
    local_version = data.get('local_version', 0)
    machine_id = data.get('machine_id', 'unknown')

    print(f"[SYNC] 用户 {user_id} 机器 {machine_id} 请求同步，本地版本: {local_version}")

    server_version = load_version()

    # 记录设备
    if machine_id:
        update_device_log(machine_id)

    # 如果客户端版本小于服务器版本，返回新配置
    if local_version < server_version:
        config = load_config()
        print(f"[SYNC] 返回新配置，版本 {server_version}")
        return jsonify({
            "updated": True,
            "config": config,
            "version": server_version
        })

    print(f"[SYNC] 配置已是最新")
    return jsonify({"updated": False})

@app.route('/api/config/push/<user_id>', methods=['POST'])
def push_config(user_id):
    """
    推送配置（客户端上传）

    请求体:
    {
        "config": {...},
        "local_version": 123,
        "machine_id": "abc123"
    }

    响应:
    {
        "success": true,
        "new_version": 124,
        "message": "配置已更新"
    }
    或
    {
        "success": false,
        "message": "本地版本过旧",
        "server_version": 124
    }
    """
    data = request.json or {}
    config = data.get('config', {})
    local_version = data.get('local_version', 0)
    machine_id = data.get('machine_id', 'unknown')

    print(f"[PUSH] 用户 {user_id} 机器 {machine_id} 推送配置，本地版本: {local_version}")

    server_version = load_version()

    # 版本冲突检测
    if local_version < server_version:
        print(f"[PUSH] 拒绝：客户端版本过旧 ({local_version} < {server_version})")
        return jsonify({
            "success": False,
            "message": "本地版本过旧，请先拉取最新配置",
            "server_version": server_version
        }), 409

    # 保存配置
    save_config(config)

    # 版本号+1
    new_version = server_version + 1
    save_version(new_version)

    # 记录设备
    if machine_id:
        update_device_log(machine_id)

    print(f"[PUSH] 成功，新版本: {new_version}")
    return jsonify({
        "success": True,
        "new_version": new_version,
        "message": "配置已更新"
    })

@app.route('/api/config/get/<user_id>', methods=['GET'])
def get_config(user_id):
    """获取当前配置（不修改版本）"""
    config = load_config()
    version = load_version()
    return jsonify({
        "config": config,
        "version": version
    })

@app.route('/api/devices/<user_id>', methods=['GET'])
def get_devices(user_id):
    """获取设备列表"""
    devices = load_devices()
    return jsonify({
        "user_id": user_id,
        "devices": devices
    })

@app.route('/api/admin/clear', methods=['POST'])
def admin_clear():
    """清空所有数据（需要密码）"""
    secret = request.args.get('secret', '')
    if secret != ADMIN_PASSWORD:
        return jsonify({"error": "无权限，密码错误"}), 403

    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    if os.path.exists(VERSION_FILE):
        os.remove(VERSION_FILE)
    if os.path.exists(DEVICES_FILE):
        os.remove(DEVICES_FILE)

    return jsonify({"success": True, "message": "所有数据已清空"})

@app.route('/api/admin/info', methods=['GET'])
def admin_info():
    """查看服务器信息（需要密码）"""
    secret = request.args.get('secret', '')
    if secret != ADMIN_PASSWORD:
        return jsonify({"error": "无权限，密码错误"}), 403

    return jsonify({
        "config": load_config(),
        "version": load_version(),
        "devices": load_devices(),
        "data_dir": os.path.abspath(DATA_DIR)
    })

if __name__ == '__main__':
    ensure_data_dir()

    print("=" * 60)
    print("游戏存档助手 - 同步服务器")
    print("=" * 60)
    print(f"数据目录: {os.path.abspath(DATA_DIR)}")
    print(f"当前版本: {load_version()}")
    print(f"管理密码: {ADMIN_PASSWORD}")
    print("")
    print("API 端点:")
    print("  GET  /api/health - 健康检查")
    print("  POST /api/config/sync/<user_id> - 同步配置（拉取）")
    print("  POST /api/config/push/<user_id> - 推送配置")
    print("  GET  /api/config/get/<user_id> - 获取配置")
    print("  GET  /api/devices/<user_id> - 查看设备列表")
    print("")
    print(f"管理接口（密码: {ADMIN_PASSWORD}）:")
    print(f"  POST /api/admin/clear?secret={ADMIN_PASSWORD} - 清空数据")
    print(f"  GET  /api/admin/info?secret={ADMIN_PASSWORD} - 查看信息")
    print("=" * 60)
    print("")

    app.run(host='0.0.0.0', port=5000, debug=True)
