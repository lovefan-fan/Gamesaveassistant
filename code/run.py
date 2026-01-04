import json
import shutil
import os
import subprocess
import sys
import threading
import time
import webbrowser
import uuid
import hashlib
import requests
from tkinter import ttk, filedialog, messagebox,Listbox, Button
from tkinter.scrolledtext import ScrolledText

import psutil
import tkinter as tk
from dotenv import load_dotenv, set_key

# 加载.env文件
def load_env():
    env_path = ".env"
    if not os.path.exists(env_path):
        # 创建默认.env文件
        default_backup_dir = os.path.join(os.environ['USERPROFILE'], "AppData", "Local", "Gamesavebackup")
        with open(env_path, 'w') as f:
            f.write(f"BACKUP_DIR={default_backup_dir}")
    load_dotenv(env_path)
    return os.getenv('BACKUP_DIR', os.path.join(os.environ['USERPROFILE'], "AppData", "Local", "Gamesavebackup"))

# 初始化环境变量
backup_dir = load_env()
cache_dir = os.path.join(backup_dir, "null")
unzip_dir = backup_dir

#=================== 网络同步配置模块 ===================#

def get_machine_id():
    """生成基于机器MAC地址的唯一标识"""
    try:
        mac = uuid.getnode()
        return hashlib.sha256(str(mac).encode()).hexdigest()[:16]
    except:
        return hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]

def get_user_config_path():
    """获取用户配置目录"""
    config_dir = os.path.join(backup_dir, "user_config")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    return config_dir

class NetworkConfigManager:
    """网络配置管理器"""

    def __init__(self):
        self.config_file = "data/network_config.json"
        self.sync_status = {"last_sync": None, "status": "未同步", "conflicts": []}
        self.load_network_config()

    def load_network_config(self):
        """加载网络配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "enabled": False,
            "server_url": "",
            "user_id": "",
            "machine_id": get_machine_id(),
            "sync_interval": 300,  # 5分钟自动同步
            "last_version": 0
        }

    def save_network_config(self, config):
        """保存网络配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def get_server_url(self):
        """获取服务器URL"""
        config = self.load_network_config()
        return config.get("server_url", "").rstrip('/')

    def get_user_id(self):
        """获取用户ID"""
        config = self.load_network_config()
        return config.get("user_id", "")

    def get_machine_id(self):
        """获取机器ID"""
        config = self.load_network_config()
        return config.get("machine_id", "")

    def is_enabled(self):
        """检查网络同步是否启用"""
        config = self.load_network_config()
        return config.get("enabled", False)

    def test_connection(self, server_url):
        """测试服务器连接"""
        try:
            response = requests.get(f"{server_url.rstrip('/')}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def sync_pull(self, log_callback=None):
        """从服务器拉取配置"""
        if not self.is_enabled():
            return False, "网络同步未启用"

        config = self.load_network_config()
        server_url = config["server_url"]
        user_id = config["user_id"]
        machine_id = config["machine_id"]
        local_version = config.get("last_version", 0)

        try:
            # 调用同步接口
            response = requests.post(
                f"{server_url.rstrip('/')}/api/config/sync/{user_id}",
                json={
                    "local_version": local_version,
                    "machine_id": machine_id
                },
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("updated"):
                    remote_config = result["config"]
                    new_version = result["version"]

                    # 保存远程配置到本地
                    with open("data/config.json", 'w', encoding='utf-8') as f:
                        json.dump(remote_config, f, indent=4, ensure_ascii=False)

                    # 更新版本号
                    config["last_version"] = new_version
                    self.save_network_config(config)

                    msg = f"同步成功：已更新到版本 {new_version}"
                    if log_callback:
                        log_callback(msg)
                    return True, msg
                else:
                    msg = "配置已是最新版本"
                    if log_callback:
                        log_callback(msg)
                    return True, msg
            else:
                msg = f"服务器错误: HTTP {response.status_code}"
                if log_callback:
                    log_callback(msg)
                return False, msg

        except requests.exceptions.ConnectionError:
            msg = "无法连接到服务器"
            if log_callback:
                log_callback(msg)
            return False, msg
        except Exception as e:
            msg = f"同步失败: {str(e)}"
            if log_callback:
                log_callback(msg)
            return False, msg

    def sync_push(self, log_callback=None):
        """推送本地配置到服务器"""
        if not self.is_enabled():
            return False, "网络同步未启用"

        config = self.load_network_config()
        server_url = config["server_url"]
        user_id = config["user_id"]
        machine_id = config["machine_id"]
        local_version = config.get("last_version", 0)

        # 读取本地配置
        local_config = load_config()
        if not local_config:
            return False, "本地配置为空"

        try:
            response = requests.post(
                f"{server_url.rstrip('/')}/api/config/push/{user_id}",
                json={
                    "config": local_config,
                    "local_version": local_version,
                    "machine_id": machine_id
                },
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                new_version = result.get("new_version", local_version)

                # 更新版本号
                config["last_version"] = new_version
                self.save_network_config(config)

                msg = f"推送成功：新版本 {new_version}"
                if log_callback:
                    log_callback(msg)
                return True, msg
            else:
                msg = f"服务器错误: HTTP {response.status_code}"
                if log_callback:
                    log_callback(msg)
                return False, msg

        except requests.exceptions.ConnectionError:
            msg = "无法连接到服务器"
            if log_callback:
                log_callback(msg)
            return False, msg
        except Exception as e:
            msg = f"推送失败: {str(e)}"
            if log_callback:
                log_callback(msg)
            return False, msg

    def sync_two_way(self, log_callback=None):
        """双向同步：先推送，再拉取"""
        if not self.is_enabled():
            return False, "网络同步未启用"

        # 先推送
        push_success, push_msg = self.sync_push(log_callback)
        if not push_success:
            return False, f"推送失败: {push_msg}"

        # 再拉取
        pull_success, pull_msg = self.sync_pull(log_callback)
        if not pull_success:
            return False, f"拉取失败: {pull_msg}"

        return True, "双向同步完成"

# 全局网络配置管理器实例
network_manager = NetworkConfigManager()

# 日志记录（线程安全）
log_text = None  # 将在主界面初始化
def log(message: str):
    """将消息写入日志文本框，并输出到控制台。线程安全。"""
    try:
        print(message)
    except Exception:
        pass
    try:
        if log_text is None:
            return
        timestamp = time.strftime('%H:%M:%S')
        def _append():
            try:
                log_text.config(state=tk.NORMAL)
                log_text.insert(tk.END, f"[{timestamp}] {message}\n")
                log_text.see(tk.END)
            finally:
                log_text.config(state=tk.DISABLED)
        # 使用主线程更新UI
        mainmenu.after(0, _append)
    except Exception:
        pass

# 可移植路径工具

def get_current_username() -> str:
    return os.environ.get('USERNAME') or os.path.basename(os.path.expanduser('~'))

def get_userprofile() -> str:
    return os.environ.get('USERPROFILE', os.path.expanduser('~'))

def _normalize_path_for_compare(p: str) -> str:
    # 统一使用绝对路径、规范分隔符、大小写（Windows不区分大小写）
    try:
        return os.path.normcase(os.path.normpath(p))
    except Exception:
        return p

def to_portable_path(path_str: str) -> str:
    """将用户目录前缀替换成占位符，便于跨机器使用。无论斜杠还是反斜杠都能正确识别，并统一输出反斜杠。"""
    if not path_str:
        return path_str
    up = get_userprofile()
    norm_path = _normalize_path_for_compare(path_str)
    norm_up = _normalize_path_for_compare(up)
    try:
        rel = os.path.relpath(norm_path, norm_up)
        # 如果在用户目录之外，rel 会以 '..' 开头
        if rel.startswith('..'):
            # 不做替换，但统一分隔符为反斜杠
            return path_str.replace('/', '\\')
        # 在用户目录内，构造 {USERPROFILE} + 相对路径
        if rel == '.' or rel == '' or rel == os.curdir:
            portable = '{USERPROFILE}'
        else:
            portable = '{USERPROFILE}' + '\\' + rel
        return portable.replace('/', '\\')
    except Exception:
        # 兜底：简单前缀判断
        if norm_path.startswith(norm_up):
            suffix = path_str[len(up):]
            return ('{USERPROFILE}' + suffix).replace('/', '\\')
        return path_str.replace('/', '\\')

def resolve_portable_path(path_str: str) -> str:
    """将配置中的占位符解析为当前机器实际路径。支持 {USERPROFILE}/{USERNAME}、~ 和环境变量。"""
    if not path_str:
        return path_str
    resolved = path_str.replace('{USERPROFILE}', get_userprofile()).replace('{USERNAME}', get_current_username())
    resolved = os.path.expandvars(resolved)
    resolved = os.path.expanduser(resolved)
    return resolved

#---方法库---
# 压缩文件夹
def compress_folder(source_folder, output_zip):
    """
    压缩指定的文件夹为ZIP格式

    :param source_folder: 要压缩的文件夹路径
    :param output_zip: 压缩文件保存的完整路径（不包括扩展名）
    """
    if not os.path.isdir(source_folder):
        raise ValueError("指定的路径不是一个有效的文件夹")

    # 获取游戏备注作为文件夹名
    config = load_config()
    game_name = None
    for name, info in config.items():
        # 使用解析后的路径进行比较，支持可移植路径
        try:
            config_path = resolve_portable_path(info[1])
        except Exception:
            config_path = info[1]
        if config_path == source_folder:  # 比较存档路径
            game_name = name
            break
    
    if not game_name:
        game_name = os.path.basename(source_folder)
    
    # 创建游戏专属文件夹
    game_dir = os.path.join(os.path.dirname(output_zip), game_name)
    if not os.path.exists(game_dir):
        os.makedirs(game_dir)
    
    # 使用文件夹名称作为文件名
    folder_name = os.path.basename(source_folder)
    output_zip = os.path.join(game_dir, folder_name)
    
    # 创建zip压缩包
    shutil.make_archive(output_zip, 'zip', source_folder)
    log(f"文件夹已成功压缩至 {output_zip}.zip")
    # 统一返回为反斜杠相对路径（例如： 魔法\\Magicraft.zip）
    relative_zip = os.path.join(game_name, folder_name + '.zip').replace('/', '\\')
    return relative_zip
    # compress_folder("./测试压缩/TSMpackagemanager", "./测试压缩/解压目录")
# 解压
def extract_zip(zip_path, extract_to=None):
    """
    解压 ZIP 文件到指定目录

    :param zip_path: ZIP 文件的路径
    :param extract_to: 解压后的文件保存路径。默认为ZIP文件所在目录
    """
    if not os.path.isfile(zip_path):
        raise ValueError("指定的路径不是一个有效的文件")

    # 如果没有指定解压路径，则使用zip文件所在的目录
    if extract_to is None:
        extract_to = os.path.splitext(zip_path)[0]  # 以压缩文件名创建文件夹

    # 解压文件
    shutil.unpack_archive(zip_path, extract_to)
    log(f"文件已成功解压至 {extract_to}")
    # extract_zip("./测试压缩/解压目录.zip", "./测试压缩/")

# 加载配置文件
def load_config(file_path="data/config.json"):
    """
    读取 JSON 配置文件的内容。如果文件不存在，则返回 None。
    """
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return None
# 创建配置文件
def create_default_config(file_path="data/config.json", default_config=None):
    """
    创建一个默认的 JSON 配置文件，如果文件不存在。
    可以传递一个默认配置的字典，如果没有提供，则使用预定义的默认配置。
    """
    if default_config is None:
        default_config = {

        }

    # 提取文件目录
    directory = os.path.dirname(file_path)

    # 如果目录不存在，创建目录
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 如果文件不存在，创建文件并写入默认配置
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(default_config, file, indent=4, ensure_ascii=False)
#更新json方法
def update_config_value(key, value, file_path="data/config.json"):
    """
    更新 JSON 配置文件中指定键的值。
    如果文件不存在，自动创建默认配置文件并更新指定值。
    """
    # 读取现有配置
    with open(file_path, 'r', encoding='utf-8') as file:
        config = json.load(file)

    # 更新指定键的值
    config[key] = value

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=4, ensure_ascii=False)

# 从配置中删除键
def delete_key_from_json(key, file_path="data/config.json"):
    """
    从 JSON 配置文件中删除指定键。
    若键不存在则不作处理。
    """
    if not os.path.exists(file_path):
        return False
    with open(file_path, 'r', encoding='utf-8') as file:
        config = json.load(file)
    if key in config:
        del config[key]
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(config, file, indent=4, ensure_ascii=False)
        return True
    return False

def add_value_to_dict_list(target_dict, key, value):
    """
    向指定字典的值列表中增加值，如果当前值与列表中最后一个值相同，则不添加。
    """
    if key not in target_dict:
        target_dict[key] = []  # 如果键不存在，则创建一个空列表

    # 检查当前值是否与列表中最后一个值相同
    if target_dict[key] and target_dict[key][-1] == value:
        pass
        # print(f"值 '{value}' 已存在，未进行追加。")
    else:
        target_dict[key].append(value)  # 将值添加到列表中

# 判断式监控
def monitor_process_if(process_name):
    """
    首次检测到指定名称的进程后，进行 5 秒检测。
    如果 5 秒后进程不再存在，则退出监控。

    :param process_name: 进程的名称
    """
    # print(f"开始监控进程: {process_name}")

    # 检查是否能首次检测到进程
    while True:
        process_found = False
        for process in psutil.process_iter(['name']):
            if process.info['name'] == process_name:
                process_found = True
                break

        # 若首次检测到进程，则等待 5 秒再重新确认
        if process_found:
            pass
            # print(f"检测到进程 {process_name}，开始 5 秒监控...")
            time.sleep(5)

            # 5 秒后再次确认进程是否还在运行
            process_running = False
            for process in psutil.process_iter(['name']):
                if process.info['name'] == process_name:
                    process_running = True
                    break

            if not process_running:
                # print(f"进程 {process_name} 已结束，退出监控。")
                break
        else:
            time.sleep(1)  # 如果未检测到进程，每秒检查一次
# 列出当前游戏进程
def list_visible_app_processes():
    """
    获取当前所有正在运行的应用程序进程名称并返回列表

    :return: 包含所有可见的应用程序进程名称的列表
    """
    app_process_list = []

    for proc in psutil.process_iter(['name', 'pid']):
        try:
            # 检查进程是否有可见窗口
            if proc.info['name'] and proc.info['name'].endswith('.exe'):
                # 只添加可见的进程
                if proc.status() == psutil.STATUS_RUNNING and proc.is_running():
                    if proc.num_handles() > 0:  # 检查是否有句柄，基本上是个简单的判断
                        app_process_list.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return list(set(app_process_list))  # 使用 set 去重

# 选择目录
def select_directory(title):
    # 创建根窗口，但不显示它
    root = tk.Tk()
    root.withdraw()  # 隐藏根窗口

    # 打开目录选择对话框
    selected_directory = filedialog.askdirectory(title=title)

    # 打印选中的目录
    if selected_directory:
        return selected_directory
    else:
        messagebox.showerror('错误','没有选择目录')
        sys.exit(1)  # 终止程序运行并返回状态码1
# 选择zip文件
def select_zip_file(title):
    """
    打开一个文件选择对话框，让用户选择一个 ZIP 文件。

    :param title: 对话框的标题
    :return: 用户选择的 ZIP 文件路径
    """
    # 创建根窗口，但不显示它
    root = tk.Tk()
    root.withdraw()  # 隐藏根窗口

    # 打开文件选择对话框，并限制只选择 ZIP 文件
    selected_file = filedialog.askopenfilename(
        title=title,
        filetypes=[["ZIP 文件", "*.zip"]]
    )

    # 返回选中的文件或显示错误消息并退出程序
    if selected_file:
        return selected_file
    else:
        messagebox.showerror('错误', '没有选择 ZIP 文件')
        sys.exit(1)  # 终止程序运行并返回状态码 1

# 选择操作的游戏
def show_keys_from_config(config, callback):
    """
    创建一个顶层窗口来展示字典中的所有键，用户选中后返回该键

    :param config: 字典变量
    :param callback: 选中后调用的回调函数
    """
    def on_select():
        selected_key = listbox.get(tk.ACTIVE)  # 获取选中的键
        callback(selected_key)  # 调用回调函数并传递选中的键
        key_window.destroy()  # 关闭窗口

    # 创建顶层窗口
    key_window = tk.Toplevel()
    key_window.title("选择操作的游戏")

    # 创建列表框并添加字典中的键
    listbox = Listbox(key_window, width=50, height=15)
    listbox.pack(pady=10)

    for key in config.keys():
        listbox.insert(tk.END, key)

    # 创建选择按钮
    select_button = Button(key_window, text="选择", command=on_select)
    select_button.pack(pady=5)

    # 运行顶层窗口的主循环
    key_window.transient(mainmenu)  # 设置为根窗口的临时窗口
    key_window.grab_set()  # 使窗口成为模态窗口

# 网络设置窗口
def network_settings():
    """网络同步设置窗口"""
    settings_window = tk.Toplevel()
    settings_window.title('网络同步设置')
    settings_window.geometry("500x420")  # 增加高度

    # 加载当前配置
    config = network_manager.load_network_config()

    # 变量
    enabled_var = tk.BooleanVar(value=config.get("enabled", False))
    server_url_var = tk.StringVar(value=config.get("server_url", ""))
    user_id_var = tk.StringVar(value=config.get("user_id", ""))
    machine_id_var = tk.StringVar(value=config.get("machine_id", ""))
    sync_interval_var = tk.IntVar(value=config.get("sync_interval", 300))

    # 状态显示
    status_label = tk.Label(settings_window, text="", font=('微软雅黑', 9), fg="blue")
    status_label.pack(pady=5)

    # 启用开关
    tk.Checkbutton(settings_window, text="启用网络同步", variable=enabled_var, font=('微软雅黑', 11)).pack(pady=5)

    # 服务器URL
    tk.Label(settings_window, text="服务器地址 (http://ip:port):", font=('微软雅黑', 10)).pack(pady=(10, 0))
    server_entry = tk.Entry(settings_window, width=50, textvariable=server_url_var)
    server_entry.pack(pady=5)

    # 用户ID
    tk.Label(settings_window, text="用户ID (不同用户用不同ID):", font=('微软雅黑', 10)).pack(pady=(10, 0))
    user_entry = tk.Entry(settings_window, width=50, textvariable=user_id_var)
    user_entry.pack(pady=5)

    # 机器ID（只读显示）
    tk.Label(settings_window, text="本机标识 (自动分配):", font=('微软雅黑', 10)).pack(pady=(10, 0))
    machine_entry = tk.Entry(settings_window, width=50, textvariable=machine_id_var, state='readonly')
    machine_entry.pack(pady=5)

    # 同步间隔
    tk.Label(settings_window, text="自动同步间隔(秒):", font=('微软雅黑', 10)).pack(pady=(10, 0))
    interval_entry = tk.Entry(settings_window, width=20, textvariable=sync_interval_var)
    interval_entry.pack(pady=5)

    def test_connection():
        """测试连接"""
        server_url = server_url_var.get().strip()
        if not server_url:
            status_label.config(text="请输入服务器地址", fg="red")
            return

        status_label.config(text="正在测试连接...", fg="orange")
        settings_window.update()

        if network_manager.test_connection(server_url):
            status_label.config(text="✓ 连接成功", fg="green")
        else:
            status_label.config(text="✗ 连接失败，请检查服务器", fg="red")

    def save_config():
        """保存配置"""
        new_config = {
            "enabled": enabled_var.get(),
            "server_url": server_url_var.get().strip(),
            "user_id": user_id_var.get().strip(),
            "machine_id": machine_id_var.get(),
            "sync_interval": sync_interval_var.get(),
            "last_version": config.get("last_version", 0)
        }

        if new_config["enabled"] and (not new_config["server_url"] or not new_config["user_id"]):
            messagebox.showerror("错误", "启用网络同步时，服务器地址和用户ID不能为空")
            return

        network_manager.save_network_config(new_config)
        messagebox.showinfo("成功", "网络配置已保存")
        log(f"网络配置已更新: 启用={new_config['enabled']}, 用户={new_config['user_id']}")
        settings_window.destroy()

    # 按钮区域
    btn_frame = tk.Frame(settings_window)
    btn_frame.pack(pady=20)  # 增加底部间距

    ttk.Button(btn_frame, text="测试连接", command=test_connection, padding=(10, 5)).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="保存配置", command=save_config, padding=(10, 5)).pack(side=tk.LEFT, padx=5)

# 同步管理窗口
def sync_manager():
    """同步管理窗口"""
    sync_window = tk.Toplevel()
    sync_window.title('配置同步管理')
    sync_window.geometry("500x300")

    # 状态显示区域
    status_frame = tk.Frame(sync_window)
    status_frame.pack(pady=10, fill=tk.X, padx=20)

    status_text = tk.Text(status_frame, height=8, width=60, font=('微软雅黑', 9))
    status_text.pack()

    def update_status(msg):
        """更新状态显示"""
        status_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        status_text.see(tk.END)

    def check_network_enabled():
        """检查网络是否启用"""
        if not network_manager.is_enabled():
            messagebox.showwarning("警告", "网络同步未启用，请先在【网络设置】中启用并配置")
            return False
        return True

    def do_pull():
        """执行拉取"""
        if not check_network_enabled():
            return
        update_status("开始拉取配置...")
        threading.Thread(target=lambda: network_manager.sync_pull(update_status), daemon=True).start()

    def do_push():
        """执行推送"""
        if not check_network_enabled():
            return
        update_status("开始推送配置...")
        threading.Thread(target=lambda: network_manager.sync_push(update_status), daemon=True).start()

    def do_two_way():
        """执行双向同步"""
        if not check_network_enabled():
            return
        update_status("开始双向同步...")
        threading.Thread(target=lambda: network_manager.sync_two_way(update_status), daemon=True).start()

    def show_server_info():
        """显示服务器信息"""
        config = network_manager.load_network_config()
        info = f"""当前配置:
- 服务器: {config.get('server_url', '未设置')}
- 用户ID: {config.get('user_id', '未设置')}
- 机器ID: {config.get('machine_id', '未生成')}
- 同步状态: {'已启用' if config.get('enabled') else '未启用'}
- 本地版本: {config.get('last_version', 0)}"""
        messagebox.showinfo("服务器信息", info)

    # 按钮区域
    btn_frame = tk.Frame(sync_window)
    btn_frame.pack(pady=15)

    btn_width = 15
    ttk.Button(btn_frame, text="拉取配置(下载)", command=do_pull, width=btn_width).grid(row=0, column=0, padx=5, pady=5)
    ttk.Button(btn_frame, text="推送配置(上传)", command=do_push, width=btn_width).grid(row=0, column=1, padx=5, pady=5)
    ttk.Button(btn_frame, text="双向同步", command=do_two_way, width=btn_width).grid(row=1, column=0, padx=5, pady=5)
    ttk.Button(btn_frame, text="查看服务器信息", command=show_server_info, width=btn_width).grid(row=1, column=1, padx=5, pady=5)

    update_status("准备就绪，请选择同步操作")
    update_status("提示：双向同步会先上传本地配置，再下载远程配置")

#---运行方法库---
# 添加游戏监控
def Addgame():
    Addgamewindow = tk.Toplevel()
    Addgamewindow.title('添加游戏监控')

    # 初始化环境变量
    process = tk.StringVar()
    notes = tk.StringVar()
    Archivedirectory = tk.StringVar()
    appid = tk.StringVar()

    # 设置游戏存档目录
    def run():
        game_path = select_directory("选择游戏存档目录")
        Archivedirectory.set(game_path)

    # 添加
    def run2():
        # 保存为可移植路径
        portable_path = to_portable_path(Archivedirectory.get())
        # 初始化4个槽位，最后一个为最近备份相对路径
        value = [process.get(), portable_path, appid.get(), ""]
        update_config_value(notes.get(), value)
        messagebox.showinfo('成功','添加成功')
        log(f"已添加监控: {notes.get()} | 进程={process.get()} | 存档目录={Archivedirectory.get()}")
    # 运行查看所有进程
    def Viewallprocesses():
        try:
            log('打开进程查看工具')
            subprocess.Popen(["./Viewallprocesses.exe"])
            # subprocess.Popen(['python',"code/process.py"])
        except FileNotFoundError as e:
            messagebox.showerror('错误','您没有下载查看进程助手,稍后将为您跳转下载，放到当前目录即可')
            # webbrowser.open('https://github.com/yxsj245/Gamesaveassistant/releases')

    # 主菜单
    tk.Label(Addgamewindow, text='输入游戏进程：', font=('微软雅黑', 12)).grid(row=1, column=1)
    ttk.Button(Addgamewindow, text='运行查看所有进程', command=Viewallprocesses, padding=(5, 5)).grid(row=1, column=3)
    tk.Entry(Addgamewindow, width=20, font=('微软雅黑', 12), textvariable=process).grid(row=1, column=2)

    tk.Label(Addgamewindow, text='设置游戏备注：', font=('微软雅黑', 12)).grid(row=2, column=1)
    tk.Entry(Addgamewindow, width=20, font=('微软雅黑', 12), textvariable=notes).grid(row=2, column=2)

    tk.Label(Addgamewindow, text='设置游戏存档目录：', font=('微软雅黑', 12)).grid(row=3, column=1)
    tk.Entry(Addgamewindow, width=70, font=('微软雅黑', 12), textvariable=Archivedirectory).grid(row=3, column=2)
    ttk.Button(Addgamewindow, text='更改目录', command=run, padding=(5, 5)).grid(row=3, column=3)

    tk.Label(Addgamewindow, text='输入游戏APPID(可选，不输入则无法进入流程模式)：', font=('微软雅黑', 12)).grid(row=4, column=1)
    tk.Entry(Addgamewindow, width=10, font=('微软雅黑', 12), textvariable=appid).grid(row=4, column=2)

    ttk.Button(Addgamewindow, text='确认添加', command=run2, padding=(10, 5)).grid(row=5, column=1)

# 修改游戏监控
def modifygame():
    config = load_config()
    def handle_selected_key(selected_key):
        modifygamewindow = tk.Toplevel()
        modifygamewindow.title('添加游戏监控')

        # 初始化环境变量
        process = tk.StringVar()
        process.set(config[selected_key][0])
        notes = tk.StringVar()
        notes.set(selected_key)
        Archivedirectory = tk.StringVar()
        # 显示解析后的实际路径，便于用户识别
        Archivedirectory.set(resolve_portable_path(config[selected_key][1]))
        appid = tk.StringVar()
        appid.set(config[selected_key][2])

        # 设置游戏存档目录
        def run():
            game_path = select_directory("选择游戏存档目录")
            Archivedirectory.set(game_path)

        # 添加
        def run2():
            # 保存为可移植路径，并保留已有的最近备份信息
            portable_path = to_portable_path(Archivedirectory.get())
            existing = config.get(selected_key, ["", "", "", ""])
            value = [process.get(), portable_path, appid.get(), existing[3] if len(existing) > 3 else ""]
            update_config_value(notes.get(), value)
            if selected_key != notes.get():
                delete_key_from_json(selected_key)
            messagebox.showinfo('成功', '修改成功')
            log(f"已修改监控: {selected_key} -> {notes.get()} | 进程={process.get()} | 存档目录={Archivedirectory.get()}")

        # 运行查看所有进程
        def Viewallprocesses():
            try:
                subprocess.Popen(["查看所有进程.exe"])
                # subprocess.Popen(['python',"process.py"])
            except FileNotFoundError as e:
                messagebox.showerror('错误', '您没有下载查看进程助手,稍后将为您跳转下载，放到当前目录即可')
                webbrowser.open('https://github.com/yxsj245/Gamesaveassistant/releases')

        # 主菜单
        tk.Label(modifygamewindow, text='输入游戏进程：', font=('微软雅黑', 12)).grid(row=1, column=1)
        ttk.Button(modifygamewindow, text='运行查看所有进程', command=Viewallprocesses, padding=(5, 5)).grid(row=1,
                                                                                                          column=3)
        tk.Entry(modifygamewindow, width=20, font=('微软雅黑', 12), textvariable=process).grid(row=1, column=2)

        tk.Label(modifygamewindow, text='设置游戏备注：', font=('微软雅黑', 12)).grid(row=2, column=1)
        tk.Entry(modifygamewindow, width=20, font=('微软雅黑', 12), textvariable=notes).grid(row=2, column=2)

        tk.Label(modifygamewindow, text='设置游戏存档目录：', font=('微软雅黑', 12)).grid(row=3, column=1)
        tk.Entry(modifygamewindow, width=70, font=('微软雅黑', 12), textvariable=Archivedirectory).grid(row=3, column=2)
        ttk.Button(modifygamewindow, text='更改目录', command=run, padding=(5, 5)).grid(row=3, column=3)

        tk.Label(modifygamewindow, text='输入游戏APPID(可选，不输入则无法进入流程模式)：', font=('微软雅黑', 12)).grid(row=4,
                                                                                                                  column=1)
        tk.Entry(modifygamewindow, width=10, font=('微软雅黑', 12), textvariable=appid).grid(row=4, column=2)

        ttk.Button(modifygamewindow, text='确认修改', command=run2, padding=(10, 5)).grid(row=5, column=1)
    show_keys_from_config(config,handle_selected_key)

# 全局变量用于跟踪正在监控的游戏
monitoring_games = {}
monitoring_enabled = True  # 全局监控开关
auto_restart_timer = None  # 自动重启定时器

# 设置备份路径
def set_backup_path():
    global backup_dir, cache_dir, unzip_dir
    # 创建设置窗口
    path_window = tk.Toplevel()
    path_window.title('设置备份路径')
    path_window.geometry("500x150")
    
    # 创建路径输入框
    path_var = tk.StringVar()
    path_var.set(backup_dir)
    path_entry = tk.Entry(path_window, width=50, textvariable=path_var)
    path_entry.pack(pady=20)
    
    # 创建选择目录按钮
    def select_path():
        selected_path = filedialog.askdirectory(title="选择备份目录")
        if selected_path:
            path_var.set(selected_path)
    
    select_button = ttk.Button(path_window, text="选择目录", command=select_path)
    select_button.pack(pady=10)
    
    # 创建确认按钮
    def confirm():
        global backup_dir, cache_dir, unzip_dir
        new_path = path_var.get()
        if new_path and os.path.isdir(new_path):
            backup_dir = new_path
            cache_dir = os.path.join(backup_dir, "null")
            unzip_dir = backup_dir
            # 更新.env文件
            set_key('.env', 'BACKUP_DIR', new_path)
            messagebox.showinfo('成功', '备份路径设置成功')
            log(f"备份路径设置为: {new_path}")
            path_window.destroy()
        else:
            messagebox.showerror('错误', '请选择有效的目录')
    
    confirm_button = ttk.Button(path_window, text="确认", command=confirm)
    confirm_button.pack(pady=10)

# 自动恢复监控
def auto_restart_monitoring():
    global auto_restart_timer, monitoring_enabled
    if not monitoring_enabled:  # 如果监控是关闭状态
        monitoring_enabled = True  # 先设置监控状态为开启
        start_all_monitoring()
        but1.config(text='停止监控', state=tk.NORMAL)
    auto_restart_timer = None  # 清除定时器

# 持续监控函数
def continuous_monitor(process_name, game_name, archive_path):
    """
    持续监控指定进程,等待游戏启动,并在游戏关闭时自动备份存档
    
    :param process_name: 进程名称
    :param game_name: 游戏名称
    :param archive_path: 存档路径
    """
    while monitoring_enabled:  # 检查全局监控开关
        # 等待游戏启动
        while monitoring_enabled:  # 检查全局监控开关
            process_found = False
            for process in psutil.process_iter(['name']):
                if process.info['name'] == process_name:
                    process_found = True
                    break
            
            if process_found:
                break
                
            time.sleep(5)  # 每5秒检查一次
        
        # 监控游戏运行状态
        while monitoring_enabled:  # 检查全局监控开关
            process_found = False
            for process in psutil.process_iter(['name']):
                if process.info['name'] == process_name:
                    process_found = True
                    break
            
            if not process_found:
                # 进程已关闭,执行备份
                try:
                    resolved_dir = resolve_portable_path(archive_path)
                    if not os.path.isdir(resolved_dir):
                        log(f"自动备份跳过：存档目录不存在: {resolved_dir}")
                        break
                    nameFile = compress_folder(resolved_dir, cache_dir)
                    # 更新配置文件,只保存最新的存档文件名
                    config = load_config()
                    if game_name in config:
                        game_config = config[game_name]
                        # 确保配置项有足够的元素
                        while len(game_config) < 4:
                            game_config.append("")
                        game_config[3] = nameFile  # 更新存档文件名
                        update_config_value(game_name, game_config)
                        log(f"自动备份成功: {game_name} -> {nameFile}")
                except Exception as e:
                    log(f"自动备份失败 {game_name}: {str(e)}")
                break
                
            time.sleep(5)  # 每5秒检查一次

# 启动所有游戏的监控
def start_all_monitoring():
    global monitoring_enabled
    monitoring_enabled = True
    config = load_config()
    for game_name in config:
        if game_name not in monitoring_games:
            monitoring_games[game_name] = True
            thread = threading.Thread(
                target=continuous_monitor,
                args=(config[game_name][0], game_name, config[game_name][1])
            )
            thread.daemon = True  # 设置为守护线程
            thread.start()
            try:
                log(f"开始监控: {game_name} | 进程={config[game_name][0]}")
            except Exception:
                pass

# 停止所有游戏的监控
def stop_all_monitoring():
    global monitoring_enabled, auto_restart_timer
    monitoring_enabled = False
    monitoring_games.clear()
    but1.config(text='停止监控', state=tk.NORMAL)
    log('已停止所有监控')
    
    # 设置60秒后自动恢复监控
    if auto_restart_timer is None:  # 确保只有一个定时器
        auto_restart_timer = mainmenu.after(60000, auto_restart_monitoring)  # 60000ms = 60s

# 运行游戏监控
def monitor():
    global monitoring_enabled, auto_restart_timer
    if monitoring_enabled:
        # 如果监控是开启状态,则停止监控
        stop_all_monitoring()
        but1.config(text='启动监控', state=tk.NORMAL)  # 更新按钮文本为"启动监控"
    else:
        # 如果监控是关闭状态,则启动监控
        # 如果存在自动重启定时器,取消它
        if auto_restart_timer is not None:
            mainmenu.after_cancel(auto_restart_timer)
            auto_restart_timer = None
        monitoring_enabled = True  # 先设置监控状态为开启
        start_all_monitoring()
        but1.config(text='停止监控', state=tk.NORMAL)  # 更新按钮文本为"停止监控"

# 恢复存档
def RestoreArchive():
    config = load_config()
    def handle_selected_key(selected_key):
        try:
            # 获取游戏存档路径
            game_save_path = resolve_portable_path(config[selected_key][1])
            # 构建存档文件路径
            save_file = os.path.join(backup_dir, selected_key, os.path.basename(game_save_path) + '.zip')
            
            if not os.path.exists(save_file):
                messagebox.showerror('错误', f'未找到存档文件: {save_file}')
                return
                
            # 解压存档到游戏存档目录
            extract_zip(save_file, game_save_path)
            messagebox.showinfo('完毕','恢复成功')
            log(f"恢复成功: {selected_key} -> {save_file}")
        except Exception as e:
            messagebox.showerror('错误',f'恢复存档失败: {str(e)}')
            log(f"恢复失败: {selected_key} | {str(e)}")
    show_keys_from_config(config, handle_selected_key)

def Process():
    messagebox.showinfo('提示', '流程模式已暂时禁用')

# 打开存档目录
def Openarchivedirectory():
    os.startfile(unzip_dir)

# 导出所有存档
def allexport():
    File = select_directory('选择导出的位置')
    FileX = File + '\\'+'导出'
    compress_folder(unzip_dir,FileX)
    messagebox.showinfo('成功','导出完毕')
    log(f"所有存档已导出至: {FileX}.zip")
    os.startfile(File)

# 导入存档
def importsave():
    File = select_zip_file('选择导出的文件')
    extract_zip(File,unzip_dir)
    messagebox.showinfo('成功', '导入完毕')

# 删除游戏监控
def removegame():
    config = load_config()
    def run(selected_key):
        delete_key_from_json(selected_key)
        messagebox.showinfo('成功','删除成功')
        log(f"已删除监控: {selected_key}")
    show_keys_from_config(config, run)

# 手动备份存档
def handmovement():
    config = load_config()
    def handle_selected_key(selected_key):
        def main():
            try:
                but3.config(text='正在备份存档', state=tk.DISABLED)
                archive_dir = resolve_portable_path(config[selected_key][1])
                if not os.path.isdir(archive_dir):
                    raise ValueError(f"存档目录不存在: {archive_dir}")
                nameFile = compress_folder(archive_dir, cache_dir)
                # 正确更新配置的第4项（索引3）为最新存档相对路径
                latest_config = load_config()
                if selected_key in latest_config:
                    game_config = latest_config[selected_key]
                    while len(game_config) < 4:
                        game_config.append("")
                    game_config[3] = nameFile
                    update_config_value(selected_key, game_config)
                messagebox.showinfo('完毕','游戏存档已备份')
                log(f"手动备份成功: {selected_key} -> {nameFile}")
            except Exception as e:
                messagebox.showerror('错误', f'备份失败: {str(e)}')
                log(f"手动备份失败: {selected_key} | {str(e)}")
            finally:
                but3.config(text='手动备份存档', state=tk.NORMAL)
        thread1 = threading.Thread(target=main)
        thread1.start()

    show_keys_from_config(config, handle_selected_key)

# 前往GitHub查看源码
def githubweb():
    webbrowser.open("https://github.com/yxsj245/Gamesaveassistant")

# 前往Gitee查看源码
def giteeweb():
    webbrowser.open("https://gitee.com/xiao-zhu245/Gamesaveassistant")
#---主菜单---
create_default_config()
global mainmenu
mainmenu = tk.Tk()
mainmenu.geometry("550x520")  # 设置窗口大小（增加高度以显示日志）
mainmenu.minsize(550,520)
mainmenu.title('游戏存档自动备份助手1.4')

def WindowEvent():
    os._exit(0)

button_padding = (10, 5)

mainmenu.protocol('WM_DELETE_WINDOW', WindowEvent)

ttk.Button(mainmenu, text='添加游戏监控', command=Addgame, padding=button_padding).place(relx=0.2, y=40, anchor='center')
ttk.Button(mainmenu, text='修改游戏监控', command=modifygame, padding=button_padding).place(relx=0.4, y=40, anchor='center')
ttk.Button(mainmenu, text='删除游戏监控', command=removegame, padding=button_padding).place(relx=0.6, y=40, anchor='center')
but3 = ttk.Button(mainmenu, text='手动备份存档', command=handmovement, padding=button_padding)
but3.place(relx=0.8, y=40, anchor='center')
ttk.Button(mainmenu, text='导出所有存档', command=allexport, padding=button_padding).place(relx=0.2, y=90, anchor='center')
ttk.Button(mainmenu, text='导入存档', command=importsave, padding=button_padding).place(relx=0.4, y=90, anchor='center')
ttk.Button(mainmenu, text='打开存档目录', command=Openarchivedirectory, padding=button_padding).place(relx=0.6, y=90, anchor='center')
ttk.Button(mainmenu, text='设置备份路径', command=set_backup_path, padding=button_padding).place(relx=0.8, y=90, anchor='center')

# 网络同步相关按钮
ttk.Button(mainmenu, text='网络设置', command=network_settings, padding=button_padding).place(relx=0.2, y=130, anchor='center')
ttk.Button(mainmenu, text='同步管理', command=sync_manager, padding=button_padding).place(relx=0.4, y=130, anchor='center')

but1 = ttk.Button(mainmenu, text='启动监控', command=monitor, padding=(50, 5))
but1.place(relx=0.5, y=170, anchor='center')
ttk.Button(mainmenu, text='恢复存档', command=RestoreArchive, padding=(50, 5)).place(relx=0.5, y=210, anchor='center')
# 注释掉流程模式按钮
# but2 = ttk.Button(mainmenu, text='流程模式', command=Process, padding=(50, 5))
# but2.place(relx=0.5, y=220, anchor='center')

ttk.Button(mainmenu, text='前往GitHub查看原作者源码', command=githubweb, padding=(50, 5)).place(relx=0.3, y=260, anchor='center')
ttk.Button(mainmenu, text='前往Gitee查看源码', command=giteeweb, padding=(50, 5)).place(relx=0.7, y=260, anchor='center')

# 日志输出区域
log_text = ScrolledText(mainmenu, wrap=tk.WORD, state=tk.DISABLED)
log_text.place(x=10, y=300, width=530, height=200)
log('应用已启动，日志输出到此处')
log('提示：如需网络同步，请点击【网络设置】配置服务器和用户ID')

# 启动自动监控
monitoring_enabled = True  # 确保监控状态为开启
start_all_monitoring()
but1.config(text='停止监控', state=tk.NORMAL)  # 设置按钮初始状态

# 开启窗口
mainmenu.mainloop()