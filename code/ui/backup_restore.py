import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from backup.compressor import compress_folder, extract_zip
from backup.history import get_available_backups, remember_backup
from config.config_manager import delete_key_from_json, load_config
from ui.dialogs import select_directory, select_zip_file, show_backups_for_restore, show_keys_from_config
from utils.logger import get_logger
from utils.paths import (
    get_backup_dir,
    get_backup_staging_dir,
    get_unzip_dir,
    resolve_portable_path,
    set_backup_dir,
)


_LOGGER = get_logger()


def restore_archive(parent) -> None:
    """恢复指定游戏的备份。"""
    config = load_config()

    def handle_selected_key(selected_key: str) -> None:
        try:
            backups = get_available_backups(selected_key, config[selected_key])
            if not backups:
                messagebox.showerror("错误", f"未找到可恢复的存档：{selected_key}")
                return
            show_backups_for_restore(parent, selected_key, backups, lambda backup: restore_selected_backup(selected_key, backup))
        except (KeyError, OSError, ValueError) as error:
            messagebox.showerror("错误", f"读取存档列表失败：{error}")
            _LOGGER.error(f"读取存档列表失败：{selected_key} | {error}")

    def restore_selected_backup(selected_key: str, backup) -> None:
        backup_ref, save_file = backup
        try:
            game_save_path = resolve_portable_path(config[selected_key][1])
            extract_zip(save_file, game_save_path)
            messagebox.showinfo("完成", "恢复成功")
            _LOGGER.info(f"恢复成功：{selected_key} -> {backup_ref}")
        except (IndexError, OSError, ValueError) as error:
            messagebox.showerror("错误", f"恢复存档失败：{error}")
            _LOGGER.error(f"恢复失败：{selected_key} | {error}")

    show_keys_from_config(parent, config, handle_selected_key)


def manual_backup(parent, set_busy_state=None) -> None:
    """手动备份指定游戏。"""
    config = load_config()

    def handle_selected_key(selected_key: str) -> None:
        def run_backup() -> None:
            if set_busy_state:
                parent.after(0, lambda: set_busy_state(True))
            try:
                archive_dir = resolve_portable_path(config[selected_key][1])
                if not os.path.isdir(archive_dir):
                    raise ValueError(f"存档目录不存在：{archive_dir}")
                backup_ref = compress_folder(archive_dir, get_backup_staging_dir(), timestamped=True)
                remember_backup(selected_key, backup_ref)
                parent.after(0, lambda: messagebox.showinfo("完毕", "游戏存档已备份"))
                _LOGGER.info(f"手动备份成功：{selected_key} -> {backup_ref}")
            except (KeyError, IndexError, OSError, ValueError) as error:
                parent.after(0, lambda: messagebox.showerror("错误", f"备份失败：{error}"))
                _LOGGER.error(f"手动备份失败：{selected_key} | {error}")
            finally:
                if set_busy_state:
                    parent.after(0, lambda: set_busy_state(False))

        threading.Thread(target=run_backup, daemon=True).start()

    show_keys_from_config(parent, config, handle_selected_key)


def remove_game(parent) -> None:
    """删除游戏监控配置。"""
    config = load_config()

    def run(selected_key: str) -> None:
        delete_key_from_json(selected_key)
        messagebox.showinfo("成功", "删除成功")
        _LOGGER.info(f"已删除监控：{selected_key}")

    show_keys_from_config(parent, config, run)


def open_archive_directory() -> None:
    """打开备份目录。"""
    os.startfile(get_unzip_dir())


def export_all_saves(parent) -> None:
    """导出所有备份。"""
    export_dir = select_directory(parent, "选择导出的位置")
    if not export_dir:
        return

    output_path = os.path.join(export_dir, "导出")
    compress_folder(get_unzip_dir(), output_path)
    messagebox.showinfo("成功", "导出完毕")
    _LOGGER.info(f"所有存档已导出至 {output_path}.zip")
    os.startfile(export_dir)


def import_save(parent) -> None:
    """导入备份压缩包。"""
    zip_file = select_zip_file(parent, "选择导出的文件")
    if not zip_file:
        return

    extract_zip(zip_file, get_unzip_dir())
    messagebox.showinfo("成功", "导入完毕")


def set_backup_path(parent) -> None:
    """设置备份路径。"""
    path_window = tk.Toplevel(parent)
    path_window.title("设置备份路径")
    path_window.geometry("500x150")

    path_var = tk.StringVar(value=get_backup_dir())
    path_entry = tk.Entry(path_window, width=50, textvariable=path_var)
    path_entry.pack(pady=20)

    def select_path() -> None:
        selected_path = filedialog.askdirectory(parent=path_window, title="选择备份目录")
        if selected_path:
            path_var.set(selected_path)

    def confirm() -> None:
        new_path = path_var.get()
        if new_path and os.path.isdir(new_path):
            set_backup_dir(new_path)
            messagebox.showinfo("成功", "备份路径设置成功")
            _LOGGER.info(f"备份路径设置为：{new_path}")
            path_window.destroy()
        else:
            messagebox.showerror("错误", "请选择有效的目录")

    ttk.Button(path_window, text="选择目录", command=select_path).pack(pady=10)
    ttk.Button(path_window, text="确认", command=confirm).pack(pady=10)

