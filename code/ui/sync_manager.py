import time
import threading
import tkinter as tk
from tkinter import messagebox, ttk


def open_sync_manager(parent, network_manager, sync_client) -> None:
    """打开同步管理窗口。"""
    sync_window = tk.Toplevel(parent)
    sync_window.title("配置同步管理")
    sync_window.geometry("500x300")

    status_frame = tk.Frame(sync_window)
    status_frame.pack(pady=10, fill=tk.X, padx=20)

    status_text = tk.Text(status_frame, height=8, width=60, font=("微软雅黑", 9))
    status_text.pack()

    def update_status(message: str) -> None:
        def append() -> None:
            status_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
            status_text.see(tk.END)

        sync_window.after(0, append)

    def check_network_enabled() -> bool:
        if not network_manager.is_enabled():
            messagebox.showwarning("警告", "网络同步未启用，请先在“网络设置”中启用并配置")
            return False
        return True

    def run_async(action) -> None:
        threading.Thread(target=action, daemon=True).start()

    def do_pull() -> None:
        if not check_network_enabled():
            return
        update_status("开始拉取配置...")
        run_async(lambda: sync_client.sync_pull(update_status))

    def do_push() -> None:
        if not check_network_enabled():
            return
        update_status("开始推送配置...")
        run_async(lambda: sync_client.sync_push(update_status))

    def do_two_way() -> None:
        if not check_network_enabled():
            return
        update_status("开始双向同步...")
        run_async(lambda: sync_client.sync_two_way(update_status))

    def show_server_info() -> None:
        config = network_manager.get_config()
        info = (
            "当前配置：\n"
            f"- 服务器：{config.get('server_url', '未设置')}\n"
            f"- 用户 ID：{config.get('user_id', '未设置')}\n"
            f"- 机器 ID：{config.get('machine_id', '未生成')}\n"
            f"- 同步状态：{'已启用' if config.get('enabled') else '未启用'}\n"
            f"- 本地版本：{config.get('last_version', 0)}"
        )
        messagebox.showinfo("服务器信息", info)

    button_frame = tk.Frame(sync_window)
    button_frame.pack(pady=15)

    button_width = 15
    ttk.Button(button_frame, text="拉取配置(下载)", command=do_pull, width=button_width).grid(row=0, column=0, padx=5, pady=5)
    ttk.Button(button_frame, text="推送配置(上传)", command=do_push, width=button_width).grid(row=0, column=1, padx=5, pady=5)
    ttk.Button(button_frame, text="双向同步", command=do_two_way, width=button_width).grid(row=1, column=0, padx=5, pady=5)
    ttk.Button(button_frame, text="查看服务器信息", command=show_server_info, width=button_width).grid(row=1, column=1, padx=5, pady=5)

    update_status("准备就绪，请选择同步操作")
    update_status("提示：双向同步会先上传本地配置，再下载远程配置")

