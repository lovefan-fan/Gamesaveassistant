import os
import threading

from backup.compressor import compress_folder
from backup.history import remember_backup
from config.config_manager import load_config
from process.process_utils import iter_exe_processes
from utils.logger import get_logger
from utils.paths import get_backup_staging_dir, resolve_portable_path


_LOGGER = get_logger()


class BackupMonitor:
    """单线程备份监控器。"""

    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()
        self._state_lock = threading.RLock()
        self._running_states = {}
        self._enabled = False

    def is_enabled(self) -> bool:
        """返回当前监控状态。"""
        with self._state_lock:
            return self._enabled

    def start_all_monitoring(self) -> None:
        """启动统一监控线程。"""
        config = load_config()
        with self._state_lock:
            self._enabled = True
            self._stop_event.clear()
            if self._thread and self._thread.is_alive():
                return
            self._thread = threading.Thread(target=self._monitor_loop, name="gamesave-monitor", daemon=True)
            self._thread.start()

        for game_name, game_config in config.items():
            process_name = game_config[0] if len(game_config) > 0 else ""
            if process_name:
                _LOGGER.info(f"开始监控：{game_name} | 进程={process_name}")

    def stop_all_monitoring(self) -> None:
        """停止统一监控线程。"""
        with self._state_lock:
            self._enabled = False
            self._running_states.clear()
            self._stop_event.set()
        _LOGGER.info("已停止所有监控")

    def _monitor_loop(self) -> None:
        _LOGGER.info("监控线程已启动")
        while not self._stop_event.is_set():
            config = load_config()
            running_names = {process_info["name"].lower() for process_info in iter_exe_processes()}
            active_games = set()

            for game_name, game_config in config.items():
                process_name = game_config[0] if len(game_config) > 0 else ""
                archive_path = game_config[1] if len(game_config) > 1 else ""
                if not process_name or not archive_path:
                    continue

                active_games.add(game_name)
                is_running = process_name.lower() in running_names
                was_running = self._running_states.get(game_name, False)

                if is_running and not was_running:
                    _LOGGER.info(f"检测到进程出现：{process_name} (游戏：{game_name})")
                elif was_running and not is_running:
                    _LOGGER.info(f"进程已消失：{process_name} (游戏：{game_name})，开始备份...")
                    self._backup_game(game_name, archive_path)

                self._running_states[game_name] = is_running

            for stale_game in list(self._running_states.keys()):
                if stale_game not in active_games:
                    self._running_states.pop(stale_game, None)

            if self._stop_event.wait(5):
                break

        _LOGGER.info("监控线程已退出")

    def _backup_game(self, game_name: str, archive_path: str) -> None:
        """执行单个游戏的自动备份。"""
        try:
            resolved_dir = resolve_portable_path(archive_path)
            if not os.path.isdir(resolved_dir):
                _LOGGER.warning(f"自动备份跳过：存档目录不存在：{resolved_dir}")
                return

            backup_ref = compress_folder(resolved_dir, get_backup_staging_dir(), timestamped=True)
            remember_backup(game_name, backup_ref)
            _LOGGER.info(f"自动备份成功：{game_name} -> {backup_ref}")
        except (OSError, ValueError) as error:
            _LOGGER.error(f"自动备份失败：{game_name} | {error}")


_MONITOR = BackupMonitor()


def start_all_monitoring() -> None:
    """启动统一监控。"""
    _MONITOR.start_all_monitoring()


def stop_all_monitoring() -> None:
    """停止统一监控。"""
    _MONITOR.stop_all_monitoring()


def is_monitoring_enabled() -> bool:
    """获取监控开关状态。"""
    return _MONITOR.is_enabled()

