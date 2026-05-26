import tkinter as tk
from tkinter import messagebox, ttk

from utils.logger import get_logger


_LOGGER = get_logger()


def open_network_settings(parent, network_manager, sync_client) -> None:
    """打开网络同步设置窗口。"""
    settings_window = tk.Toplevel(parent)
    settings_window.title("网络同步设置")
    settings_window.geometry("500x420")

    config = network_manager.get_config()
    enabled_var = tk.BooleanVar(value=config.get("enabled", False))
    server_url_var = tk.StringVar(value=config.get("server_url", ""))
    user_id_var = tk.StringVar(value=config.get("user_id", ""))
    machine_id_var = tk.StringVar(value=config.get("machine_id", ""))
    sync_interval_var = tk.IntVar(value=config.get("sync_interval", 300))

    status_label = tk.Label(settings_window, text="", font=("微软雅黑", 9), fg="blue")
    status_label.pack(pady=5)

    tk.Checkbutton(settings_window, text="启用网络同步", variable=enabled_var, font=("微软雅黑", 11)).pack(pady=5)

    tk.Label(settings_window, text="服务器地址（http://ip:port）：", font=("微软雅黑", 10)).pack(pady=(10, 0))
    tk.Entry(settings_window, width=50, textvariable=server_url_var).pack(pady=5)

    tk.Label(settings_window, text="用户 ID（不同用户用不同 ID）：", font=("微软雅黑", 10)).pack(pady=(10, 0))
    tk.Entry(settings_window, width=50, textvariable=user_id_var).pack(pady=5)

    tk.Label(settings_window, text="本机标识（自动分配）：", font=("微软雅黑", 10)).pack(pady=(10, 0))
    tk.Entry(settings_window, width=50, textvariable=machine_id_var, state="readonly").pack(pady=5)

    tk.Label(settings_window, text="自动同步间隔（秒）：", font=("微软雅黑", 10)).pack(pady=(10, 0))
    tk.Entry(settings_window, width=20, textvariable=sync_interval_var).pack(pady=5)

    def test_connection() -> None:
        server_url = server_url_var.get().strip()
        if not server_url:
            status_label.config(text="请输入服务器地址", fg="red")
            return

        status_label.config(text="正在测试连接...", fg="orange")
        settings_window.update()
        if sync_client.test_connection(server_url):
            status_label.config(text="连接成功", fg="green")
        else:
            status_label.config(text="连接失败，请检查服务器", fg="red")

    def save_current_config() -> None:
        new_config = {
            "enabled": enabled_var.get(),
            "server_url": server_url_var.get().strip(),
            "user_id": user_id_var.get().strip(),
            "machine_id": machine_id_var.get(),
            "sync_interval": sync_interval_var.get(),
            "last_version": config.get("last_version", 0),
        }

        if new_config["enabled"] and (not new_config["server_url"] or not new_config["user_id"]):
            messagebox.showerror("错误", "启用网络同步时，服务器地址和用户 ID 不能为空")
            return

        network_manager.save_network_config(new_config)
        messagebox.showinfo("成功", "网络配置已保存")
        _LOGGER.info(f"网络配置已更新：启用={new_config['enabled']}，用户={new_config['user_id']}")
        settings_window.destroy()

    button_frame = tk.Frame(settings_window)
    button_frame.pack(pady=20)

    ttk.Button(button_frame, text="测试连接", command=test_connection, padding=(10, 5)).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="保存配置", command=save_current_config, padding=(10, 5)).pack(side=tk.LEFT, padx=5)

