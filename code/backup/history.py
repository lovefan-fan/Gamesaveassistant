import os
import time

from config.config_manager import load_config, update_config_value
from utils.logger import get_logger
from utils.paths import get_backup_dir, resolve_portable_path


MAX_RECENT_BACKUPS = 3
_LOGGER = get_logger()


def get_backup_history(game_config) -> list[str]:
    """获取某个游戏的备份历史。"""
    if len(game_config) < 4:
        return []

    history = game_config[3]
    if isinstance(history, list):
        return [item for item in history if item]
    if isinstance(history, str) and history:
        return [history]
    return []


def get_backup_abs_path(backup_ref: str, game_name: str | None = None) -> str:
    """将相对备份路径转换为绝对路径。"""
    if os.path.isabs(backup_ref):
        return backup_ref

    backup_dir = get_backup_dir()
    candidates = [os.path.join(backup_dir, backup_ref)]
    if game_name:
        reference_dir = os.path.dirname(backup_ref)
        if not reference_dir:
            candidates.append(os.path.join(backup_dir, game_name, backup_ref))
        candidates.append(os.path.join(backup_dir, game_name, os.path.basename(backup_ref)))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return candidates[0]


def get_available_backups(game_name: str, game_config) -> list[tuple[str, str]]:
    """获取可恢复的备份列表。"""
    history = get_backup_history(game_config)
    try:
        game_save_path = resolve_portable_path(game_config[1])
        legacy_ref = os.path.join(game_name, os.path.basename(game_save_path) + ".zip").replace("/", "\\")
        if legacy_ref not in history:
            history.append(legacy_ref)
    except (IndexError, OSError, ValueError):
        pass

    backups = []
    seen = set()
    for backup_ref in history:
        if backup_ref in seen:
            continue
        seen.add(backup_ref)
        backup_path = get_backup_abs_path(backup_ref, game_name)
        if os.path.exists(backup_path):
            backups.append((backup_ref, backup_path))

    backups.sort(key=lambda item: os.path.getmtime(item[1]), reverse=True)
    return backups[:MAX_RECENT_BACKUPS]


def format_backup_time(backup_path: str) -> str:
    """格式化备份文件时间。"""
    try:
        timestamp = os.path.getmtime(backup_path)
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    except OSError:
        return "未知时间"


def remember_backup(game_name: str, backup_ref: str) -> list[str]:
    """统一维护最近备份列表。"""
    config = load_config()
    if game_name not in config:
        return []

    game_config = config[game_name]
    while len(game_config) < 4:
        game_config.append("")

    history = [backup_ref]
    for existing_ref in get_backup_history(game_config):
        if existing_ref != backup_ref:
            history.append(existing_ref)

    keep_history = history[:MAX_RECENT_BACKUPS]
    for expired_ref in history[MAX_RECENT_BACKUPS:]:
        backup_path = get_backup_abs_path(expired_ref, game_name)
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                _LOGGER.info(f"已清理旧存档：{backup_path}")
        except OSError as error:
            _LOGGER.error(f"清理旧存档失败：{backup_path} | {error}")

    game_config[3] = keep_history
    update_config_value(game_name, game_config)
    return keep_history

