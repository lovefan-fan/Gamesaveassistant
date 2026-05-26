import tkinter as tk
from tkinter import Button, Listbox, filedialog, messagebox

from backup.history import format_backup_time


def select_directory(parent, title: str) -> str | None:
    """选择目录，取消时返回 None。"""
    selected_directory = filedialog.askdirectory(parent=parent, title=title)
    return selected_directory or None


def select_zip_file(parent, title: str) -> str | None:
    """选择 ZIP 文件，取消时返回 None。"""
    selected_file = filedialog.askopenfilename(parent=parent, title=title, filetypes=[("ZIP 文件", "*.zip")])
    return selected_file or None


def show_keys_from_config(parent, config: dict, callback, title: str = "选择操作的游戏") -> None:
    """展示配置中的游戏列表。"""

    def on_select() -> None:
        selected_key = listbox.get(tk.ACTIVE)
        if not selected_key:
            messagebox.showerror("错误", "请选择一个游戏")
            return
        callback(selected_key)
        key_window.destroy()

    key_window = tk.Toplevel(parent)
    key_window.title(title)

    listbox = Listbox(key_window, width=50, height=15)
    listbox.pack(pady=10, padx=10)

    for key in config.keys():
        listbox.insert(tk.END, key)

    if config:
        listbox.selection_set(0)
        listbox.activate(0)
    listbox.bind("<Double-Button-1>", lambda event: on_select())

    select_button = Button(key_window, text="选择", command=on_select)
    select_button.pack(pady=5)

    key_window.transient(parent)
    key_window.grab_set()


def show_backups_for_restore(parent, game_name: str, backups, callback) -> None:
    """展示可恢复的备份列表。"""

    def on_select() -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("错误", "请选择要恢复的存档")
            return
        callback(backups[selection[0]])
        backup_window.destroy()

    backup_window = tk.Toplevel(parent)
    backup_window.title(f"选择要恢复的存档 - {game_name}")

    listbox = Listbox(backup_window, width=80, height=10)
    listbox.pack(pady=10, padx=10)

    for backup_ref, backup_path in backups:
        label = f"{backup_ref.split(chr(92))[-1]}    {format_backup_time(backup_path)}"
        listbox.insert(tk.END, label)

    if backups:
        listbox.selection_set(0)
        listbox.activate(0)
    listbox.bind("<Double-Button-1>", lambda event: on_select())

    select_button = Button(backup_window, text="恢复选中存档", command=on_select)
    select_button.pack(pady=5)

    backup_window.transient(parent)
    backup_window.grab_set()

