import json
import threading
from pathlib import Path

from utils.logger import get_logger
from utils.paths import get_config_path


_CONFIG_LOCK = threading.RLock()
_LOGGER = get_logger()


def _resolve_config_path(file_path: str | Path | None = None) -> Path:
    """解析配置文件路径。"""
    if file_path is None:
        return get_config_path()
    return Path(file_path)


def _write_config(config_data: dict, file_path: str | Path | None = None) -> dict:
    """写入完整配置。"""
    config_path = _resolve_config_path(file_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as file:
        json.dump(config_data, file, indent=4, ensure_ascii=False)
    return config_data


def create_default_config(file_path: str | Path | None = None, default_config: dict | None = None) -> None:
    """创建默认配置文件。"""
    config_path = _resolve_config_path(file_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if default_config is None:
        default_config = {}

    with _CONFIG_LOCK:
        if not config_path.exists():
            _write_config(default_config, config_path)


def load_config(file_path: str | Path | None = None) -> dict:
    """读取配置文件。"""
    config_path = _resolve_config_path(file_path)
    create_default_config(config_path)

    with _CONFIG_LOCK:
        try:
            with config_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                return data if isinstance(data, dict) else {}
        except json.JSONDecodeError as error:
            _LOGGER.error(f"配置文件解析失败：{config_path} | {error}")
            return {}
        except OSError as error:
            _LOGGER.error(f"读取配置文件失败：{config_path} | {error}")
            return {}


def save_config(config_data: dict, file_path: str | Path | None = None) -> dict:
    """保存完整配置。"""
    with _CONFIG_LOCK:
        return _write_config(config_data, file_path)


def update_config_value(key: str, value, file_path: str | Path | None = None) -> dict:
    """更新指定配置项。"""
    with _CONFIG_LOCK:
        config_data = load_config(file_path)
        config_data[key] = value
        _write_config(config_data, file_path)
        return config_data


def delete_key_from_json(key: str, file_path: str | Path | None = None) -> bool:
    """删除指定配置项。"""
    with _CONFIG_LOCK:
        config_data = load_config(file_path)
        if key not in config_data:
            return False
        del config_data[key]
        _write_config(config_data, file_path)
        return True

