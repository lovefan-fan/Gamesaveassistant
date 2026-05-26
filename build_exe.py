#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""游戏存档自动备份助手 - 打包脚本"""

import os
import shutil
import subprocess
import sys


def install_requirements():
    """安装依赖包"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )
        print("依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"依赖包安装失败: {e}")
        return False


def build_exe():
    """使用 PyInstaller 打包 exe"""
    print("开始打包 exe 文件...")
    try:
        subprocess.check_call(["pyinstaller", "GamesaveAssistant.spec"])
        source_path = os.path.join("code", "Viewallprocesses.exe")
        target_path = os.path.join("dist", "Viewallprocesses.exe")
        if os.path.exists(source_path):
            shutil.copy2(source_path, target_path)
            print("已复制 Viewallprocesses.exe 到 dist 目录")
        else:
            print("未找到 Viewallprocesses.exe，跳过复制")
        print("exe 打包完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {e}")
        return False


def main():
    """主函数"""
    print("=== 游戏存档自动备份助手 - 打包工具 ===")

    if not install_requirements():
        print("依赖安装失败，退出打包")
        return
    if not build_exe():
        print("打包失败")
        return

    print("\n=== 打包完成 ===")
    print("exe 文件位置: dist/GamesaveAssistant.exe")


if __name__ == "__main__":
    main()
