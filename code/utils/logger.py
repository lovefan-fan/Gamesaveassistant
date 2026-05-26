import logging
import threading
import tkinter as tk

from utils.paths import get_log_file_path


LOGGER_NAME = "gamesaveassistant"
_LOGGER_LOCK = threading.RLock()
_TK_HANDLER = None


class TkinterTextHandler(logging.Handler):
    """将日志输出到 Tkinter 文本框。"""

    def __init__(self, root: tk.Misc, text_widget: tk.Text):
        super().__init__()
        self.root = root
        self.text_widget = text_widget

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)

        def append_text() -> None:
            try:
                self.text_widget.config(state=tk.NORMAL)
                self.text_widget.insert(tk.END, f"{message}\n")
                self.text_widget.see(tk.END)
                self.text_widget.config(state=tk.DISABLED)
            except tk.TclError:
                pass

        try:
            self.root.after(0, append_text)
        except tk.TclError:
            pass


def configure_logging(root: tk.Misc | None = None, text_widget: tk.Text | None = None) -> logging.Logger:
    """配置统一日志输出。"""
    global _TK_HANDLER

    with _LOGGER_LOCK:
        logger = logging.getLogger(LOGGER_NAME)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
            file_handler = logging.FileHandler(get_log_file_path(), encoding="utf-8")
            file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%H:%M:%S"))
            logger.addHandler(file_handler)

        if root is not None and text_widget is not None:
            if _TK_HANDLER is not None:
                logger.removeHandler(_TK_HANDLER)
            _TK_HANDLER = TkinterTextHandler(root, text_widget)
            _TK_HANDLER.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%H:%M:%S"))
            logger.addHandler(_TK_HANDLER)

        return logger


def get_logger() -> logging.Logger:
    """获取统一日志对象。"""
    return configure_logging()

