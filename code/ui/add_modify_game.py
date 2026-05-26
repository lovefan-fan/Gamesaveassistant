import subprocess
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk

from config.config_manager import delete_key_from_json, load_config, update_config_value
from ui.dialogs import select_directory
from utils.logger import get_logger
from utils.paths import get_viewallprocesses_path, resolve_portable_path, to_portable_path


_LOGGER = get_logger()


class GameConfigWindow(tk.Toplevel):
    """新增和修改游戏配置的统一窗口。"""

    def __init__(self, parent, mode: str = "add", selected_key: str | None = None):
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        self.selected_key = selected_key
        self.title("添加游戏监控" if mode == "add" else "修改游戏监控")

        self.process_var = tk.StringVar()
        self.notes_var = tk.StringVar()
        self.archive_dir_var = tk.StringVar()
        self.appid_var = tk.StringVar()

        self._load_initial_values()
        self._build_widgets()
        self.transient(parent)
        self.grab_set()

    def _load_initial_values(self) -> None:
        """加载编辑模式的初始值。"""
        if self.mode != "modify" or not self.selected_key:
            return

        config = load_config()
        selected_config = config.get(self.selected_key, ["", "", "", ""])
        self.process_var.set(selected_config[0] if len(selected_config) > 0 else "")
        self.notes_var.set(self.selected_key)
        self.archive_dir_var.set(resolve_portable_path(selected_config[1]) if len(selected_config) > 1 else "")
        self.appid_var.set(selected_config[2] if len(selected_config) > 2 else "")

    def _build_widgets(self) -> None:
        """构建窗口控件。"""
        tk.Label(self, text="输入游戏进程：", font=("微软雅黑", 12)).grid(row=1, column=1)
        ttk.Button(self, text="运行查看所有进程", command=self._open_process_viewer, padding=(5, 5)).grid(row=1, column=3)
        tk.Entry(self, width=20, font=("微软雅黑", 12), textvariable=self.process_var).grid(row=1, column=2)

        tk.Label(self, text="设置游戏备注：", font=("微软雅黑", 12)).grid(row=2, column=1)
        tk.Entry(self, width=20, font=("微软雅黑", 12), textvariable=self.notes_var).grid(row=2, column=2)

        tk.Label(self, text="设置游戏存档目录：", font=("微软雅黑", 12)).grid(row=3, column=1)
        tk.Entry(self, width=70, font=("微软雅黑", 12), textvariable=self.archive_dir_var).grid(row=3, column=2)
        ttk.Button(self, text="更改目录", command=self._select_archive_directory, padding=(5, 5)).grid(row=3, column=3)

        tk.Label(self, text="输入游戏 APPID（可选，不输入则无法进入流程模式）：", font=("微软雅黑", 12)).grid(row=4, column=1)
        tk.Entry(self, width=10, font=("微软雅黑", 12), textvariable=self.appid_var).grid(row=4, column=2)

        button_text = "确认添加" if self.mode == "add" else "确认修改"
        ttk.Button(self, text=button_text, command=self._save_game_config, padding=(10, 5)).grid(row=5, column=1)

    def _select_archive_directory(self) -> None:
        """选择存档目录。"""
        game_path = select_directory(self, "选择游戏存档目录")
        if game_path:
            self.archive_dir_var.set(game_path)

    def _open_process_viewer(self) -> None:
        """打开进程查看工具。"""
        process_tool = get_viewallprocesses_path()
        try:
            subprocess.Popen([str(process_tool)])
            _LOGGER.info("打开进程查看工具")
        except FileNotFoundError:
            messagebox.showerror("错误", "未找到查看进程工具，稍后将跳转到下载页面")
            webbrowser.open("https://github.com/yxsj245/Gamesaveassistant/releases")

    def _save_game_config(self) -> None:
        """保存游戏配置。"""
        portable_path = to_portable_path(self.archive_dir_var.get())
        config = load_config()

        existing_history = ""
        if self.mode == "modify" and self.selected_key:
            existing = config.get(self.selected_key, ["", "", "", ""])
            existing_history = existing[3] if len(existing) > 3 else ""

        value = [self.process_var.get(), portable_path, self.appid_var.get(), existing_history]
        update_config_value(self.notes_var.get(), value)

        if self.mode == "modify" and self.selected_key and self.selected_key != self.notes_var.get():
            delete_key_from_json(self.selected_key)

        messagebox.showinfo("成功", "添加成功" if self.mode == "add" else "修改成功")
        _LOGGER.info(
            f"{'已添加监控' if self.mode == 'add' else '已修改监控'}："
            f"{self.selected_key or self.notes_var.get()} -> {self.notes_var.get()} | "
            f"进程={self.process_var.get()} | 存档目录={self.archive_dir_var.get()}"
        )
        self.destroy()

