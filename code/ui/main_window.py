import tkinter as tk
import webbrowser
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from backup.monitor import is_monitoring_enabled, start_all_monitoring, stop_all_monitoring
from config.config_manager import create_default_config, load_config
from config.network_config import NetworkConfigManager
from network.sync_client import SyncClient
from ui.add_modify_game import GameConfigWindow
from ui.backup_restore import export_all_saves, import_save, manual_backup, open_archive_directory, remove_game, restore_archive, set_backup_path
from ui.dialogs import show_keys_from_config
from ui.network_settings import open_network_settings
from ui.sync_manager import open_sync_manager
from utils.logger import configure_logging, get_logger


class MainWindow:
    """主窗口。"""

    def __init__(self):
        create_default_config()

        self.root = tk.Tk()
        self.root.geometry("550x520")
        self.root.minsize(550, 520)
        self.root.title("游戏存档自动备份助手1.4")

        self.auto_restart_timer = None
        self.network_manager = NetworkConfigManager()
        self.sync_client = SyncClient(self.network_manager)

        self.log_text = ScrolledText(self.root, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.place(x=10, y=300, width=530, height=200)
        configure_logging(self.root, self.log_text)
        self.logger = get_logger()

        self.button_padding = (10, 5)
        self._build_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.logger.info("应用已启动，日志输出到此处")
        self.logger.info("提示：如需网络同步，请点击【网络设置】配置服务器和用户 ID")

        self.start_monitoring(initial=True)

    def _build_widgets(self) -> None:
        """构建主界面。"""
        ttk.Button(self.root, text="添加游戏监控", command=self.open_add_game, padding=self.button_padding).place(relx=0.2, y=40, anchor="center")
        ttk.Button(self.root, text="修改游戏监控", command=self.open_modify_game, padding=self.button_padding).place(relx=0.4, y=40, anchor="center")
        ttk.Button(self.root, text="删除游戏监控", command=lambda: remove_game(self.root), padding=self.button_padding).place(relx=0.6, y=40, anchor="center")

        self.manual_backup_button = ttk.Button(self.root, text="手动备份存档", command=self.open_manual_backup, padding=self.button_padding)
        self.manual_backup_button.place(relx=0.8, y=40, anchor="center")

        ttk.Button(self.root, text="导出所有存档", command=lambda: export_all_saves(self.root), padding=self.button_padding).place(relx=0.2, y=90, anchor="center")
        ttk.Button(self.root, text="导入存档", command=lambda: import_save(self.root), padding=self.button_padding).place(relx=0.4, y=90, anchor="center")
        ttk.Button(self.root, text="打开存档目录", command=open_archive_directory, padding=self.button_padding).place(relx=0.6, y=90, anchor="center")
        ttk.Button(self.root, text="设置备份路径", command=lambda: set_backup_path(self.root), padding=self.button_padding).place(relx=0.8, y=90, anchor="center")

        ttk.Button(self.root, text="网络设置", command=self.open_network_settings, padding=self.button_padding).place(relx=0.2, y=130, anchor="center")
        ttk.Button(self.root, text="同步管理", command=self.open_sync_manager, padding=self.button_padding).place(relx=0.4, y=130, anchor="center")

        self.monitor_button = ttk.Button(self.root, text="启动监控", command=self.toggle_monitoring, padding=(50, 5))
        self.monitor_button.place(relx=0.5, y=170, anchor="center")
        ttk.Button(self.root, text="恢复存档", command=lambda: restore_archive(self.root), padding=(50, 5)).place(relx=0.5, y=210, anchor="center")

        ttk.Button(self.root, text="前往 GitHub 查看原作者源码", command=self.open_github, padding=(50, 5)).place(relx=0.3, y=260, anchor="center")
        ttk.Button(self.root, text="前往 Gitee 查看源码", command=self.open_gitee, padding=(50, 5)).place(relx=0.7, y=260, anchor="center")

    def open_add_game(self) -> None:
        """打开新增游戏窗口。"""
        GameConfigWindow(self.root, mode="add")

    def open_modify_game(self) -> None:
        """打开修改游戏窗口。"""
        config = load_config()
        show_keys_from_config(self.root, config, lambda selected_key: GameConfigWindow(self.root, mode="modify", selected_key=selected_key))

    def open_manual_backup(self) -> None:
        """打开手动备份流程。"""
        manual_backup(self.root, self.set_manual_backup_busy)

    def set_manual_backup_busy(self, busy: bool) -> None:
        """更新手动备份按钮状态。"""
        if busy:
            self.manual_backup_button.config(text="正在备份存档", state=tk.DISABLED)
        else:
            self.manual_backup_button.config(text="手动备份存档", state=tk.NORMAL)

    def open_network_settings(self) -> None:
        """打开网络设置。"""
        open_network_settings(self.root, self.network_manager, self.sync_client)

    def open_sync_manager(self) -> None:
        """打开同步管理。"""
        open_sync_manager(self.root, self.network_manager, self.sync_client)

    def clear_auto_restart_timer(self) -> None:
        """取消自动恢复监控定时器。"""
        if self.auto_restart_timer is not None:
            self.root.after_cancel(self.auto_restart_timer)
            self.auto_restart_timer = None

    def auto_restart_monitoring(self) -> None:
        """自动恢复监控。"""
        if not is_monitoring_enabled():
            self.start_monitoring()
        self.auto_restart_timer = None

    def start_monitoring(self, initial: bool = False) -> None:
        """启动监控。"""
        self.clear_auto_restart_timer()
        start_all_monitoring()
        self.monitor_button.config(text="停止监控", state=tk.NORMAL)
        if not initial:
            self.logger.info("已启动监控")

    def stop_monitoring(self) -> None:
        """停止监控并安排自动恢复。"""
        stop_all_monitoring()
        self.monitor_button.config(text="启动监控", state=tk.NORMAL)
        self.clear_auto_restart_timer()
        self.auto_restart_timer = self.root.after(60000, self.auto_restart_monitoring)

    def toggle_monitoring(self) -> None:
        """切换监控状态。"""
        if is_monitoring_enabled():
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def open_github(self) -> None:
        """打开 GitHub 页面。"""
        webbrowser.open("https://github.com/yxsj245/Gamesaveassistant")

    def open_gitee(self) -> None:
        """打开 Gitee 页面。"""
        webbrowser.open("https://gitee.com/xiao-zhu245/Gamesaveassistant")

    def on_close(self) -> None:
        """关闭窗口。"""
        self.clear_auto_restart_timer()
        stop_all_monitoring()
        self.root.destroy()

    def run(self) -> None:
        """启动主循环。"""
        self.root.mainloop()

