#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏存档自动备份助手 - 打包脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_requirements():
    """安装依赖包"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖包安装完成")
    except subprocess.CalledProcessError as e:
        print(f"依赖包安装失败: {e}")
        return False
    return True

def build_exe():
    """使用PyInstaller打包exe"""
    print("开始打包exe文件...")
    
    # PyInstaller命令参数
    cmd = [
        "pyinstaller",
        "--onefile",  # 打包成单个exe文件
        "--windowed",  # 不显示控制台窗口
        "--name=游戏存档自动备份助手",  # 指定exe文件名
        "--icon=icon.ico",  # 图标文件（如果有的话）
        "--add-data=data;data",  # 包含data目录
        "--hidden-import=tkinter",
        "--hidden-import=psutil",
        "--hidden-import=dotenv",
        "code/run.py"
    ]
    
    # 如果没有图标文件，移除图标参数
    if not os.path.exists("icon.ico"):
        cmd = [arg for arg in cmd if not arg.startswith("--icon")]
    
    try:
        subprocess.check_call(cmd)
        print("exe文件打包完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {e}")
        return False

def copy_additional_files():
    """复制额外需要的文件到dist目录"""
    print("复制额外文件...")
    dist_dir = Path("dist")
    
    # 复制Viewallprocesses.exe
    if os.path.exists("code/Viewallprocesses.exe"):
        shutil.copy2("code/Viewallprocesses.exe", dist_dir / "Viewallprocesses.exe")
        print("已复制 Viewallprocesses.exe")
    
    # 复制process.py（如果需要的话）
    if os.path.exists("code/process.py"):
        shutil.copy2("code/process.py", dist_dir / "process.py")
        print("已复制 process.py")
    
    # 复制README和LICENSE
    for file in ["README.md", "LICENSE"]:
        if os.path.exists(file):
            shutil.copy2(file, dist_dir / file)
            print(f"已复制 {file}")

def create_launcher_script():
    """创建启动脚本"""
    launcher_content = '''@echo off
chcp 65001 >nul
title 游戏存档自动备份助手
echo 正在启动游戏存档自动备份助手...
"游戏存档自动备份助手.exe"
pause
'''
    
    with open("dist/启动游戏存档助手.bat", "w", encoding="utf-8") as f:
        f.write(launcher_content)
    print("已创建启动脚本: 启动游戏存档助手.bat")

def main():
    """主函数"""
    print("=== 游戏存档自动备份助手 - 打包工具 ===")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        return
    
    # 安装依赖
    if not install_requirements():
        print("依赖安装失败，退出打包")
        return
    
    # 打包exe
    if not build_exe():
        print("打包失败，退出")
        return
    
    # 复制额外文件
    copy_additional_files()
    
    # 创建启动脚本
    create_launcher_script()
    
    print("\n=== 打包完成 ===")
    print("exe文件位置: dist/游戏存档自动备份助手.exe")
    print("启动脚本: dist/启动游戏存档助手.bat")
    print("\n使用说明:")
    print("1. 将整个dist目录复制到目标机器")
    print("2. 运行 '启动游戏存档助手.bat' 或直接运行exe文件")
    print("3. 首次运行会自动创建配置文件和环境文件")

if __name__ == "__main__":
    main() 