import copy
import json
import threading
import time
import uuid
import hashlib
from pathlib import Path

from utils.paths import get_network_config_path


def get_machine_id() -> str:
    """生成基于机器信息的稳定标识。"""
    try:
        mac_address = uuid.getnode()
        return hashlib.sha256(str(mac_address).encode("utf-8")).hexdigest()[:16]
    except (AttributeError, OSError, ValueError):
        return hashlib.sha256(str(time.time()).encode("utf-8")).hexdigest()[:16]


class NetworkConfigManager:
    """网络配置管理器。"""

    def __init__(self, config_file: str | Path | None = None):
        self.config_file = Path(config_file) if config_file else get_network_config_path()
        self.sync_status = {"last_sync": None, "status": "未同步", "conflicts": []}
        self._lock = threading.RLock()
        self._config = self._load_from_disk()

    def _default_config(self) -> dict:
        return {
            "enabled": False,
            "server_url": "",
            "user_id": "",
            "machine_id": get_machine_id(),
            "sync_interval": 300,
            "last_version": 0,
        }

    def _load_from_disk(self) -> dict:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        if self.config_file.exists():
            with self.config_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, dict):
                    default_config = self._default_config()
                    default_config.update(data)
                    return default_config
        return self._default_config()

    def reload(self) -> dict:
        """重新从磁盘加载配置。"""
        with self._lock:
            self._config = self._load_from_disk()
            return copy.deepcopy(self._config)

    def load_network_config(self) -> dict:
        """兼容旧接口：从磁盘刷新并返回配置。"""
        return self.reload()

    def save_network_config(self, config: dict) -> dict:
        """保存网络配置并更新内存缓存。"""
        with self._lock:
            updated_config = self._default_config()
            updated_config.update(config)
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with self.config_file.open("w", encoding="utf-8") as file:
                json.dump(updated_config, file, indent=4, ensure_ascii=False)
            self._config = updated_config
            return copy.deepcopy(self._config)

    def get_config(self) -> dict:
        """获取当前缓存配置。"""
        with self._lock:
            return copy.deepcopy(self._config)

    def get_server_url(self) -> str:
        with self._lock:
            return self._config.get("server_url", "").rstrip("/")

    def get_user_id(self) -> str:
        with self._lock:
            return self._config.get("user_id", "")

    def get_machine_id(self) -> str:
        with self._lock:
            return self._config.get("machine_id", "")

    def get_sync_interval(self) -> int:
        with self._lock:
            return int(self._config.get("sync_interval", 300))

    def get_last_version(self) -> int:
        with self._lock:
            return int(self._config.get("last_version", 0))

    def is_enabled(self) -> bool:
        with self._lock:
            return bool(self._config.get("enabled", False))

