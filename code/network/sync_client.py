import requests

from config.config_manager import load_config, save_config
from utils.logger import get_logger


_LOGGER = get_logger()


class SyncClient:
    """网络同步客户端。"""

    def __init__(self, network_manager):
        self.network_manager = network_manager

    def _report(self, message: str, log_callback=None) -> None:
        _LOGGER.info(message)
        if log_callback:
            log_callback(message)

    def test_connection(self, server_url: str) -> bool:
        """测试服务器连通性。"""
        try:
            response = requests.get(f"{server_url.rstrip('/')}/api/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def sync_pull(self, log_callback=None):
        """从服务器拉取配置。"""
        if not self.network_manager.is_enabled():
            return False, "网络同步未启用"

        config = self.network_manager.get_config()
        server_url = config["server_url"]
        user_id = config["user_id"]
        machine_id = config["machine_id"]
        local_version = config.get("last_version", 0)

        try:
            response = requests.post(
                f"{server_url.rstrip('/')}/api/config/sync/{user_id}",
                json={"local_version": local_version, "machine_id": machine_id},
                timeout=10,
            )
            if response.status_code != 200:
                message = f"服务器错误：HTTP {response.status_code}"
                self._report(message, log_callback)
                return False, message

            result = response.json()
            if result.get("updated"):
                remote_config = result["config"]
                new_version = result["version"]
                save_config(remote_config)
                config["last_version"] = new_version
                self.network_manager.save_network_config(config)
                message = f"同步成功：已更新到版本 {new_version}"
                self._report(message, log_callback)
                return True, message

            message = "配置已经是最新版本"
            self._report(message, log_callback)
            return True, message
        except requests.exceptions.ConnectionError:
            message = "无法连接到服务器"
            self._report(message, log_callback)
            return False, message
        except requests.RequestException as error:
            message = f"同步失败：{error}"
            self._report(message, log_callback)
            return False, message
        except ValueError as error:
            message = f"同步失败：{error}"
            self._report(message, log_callback)
            return False, message

    def sync_push(self, log_callback=None):
        """将本地配置推送到服务器。"""
        if not self.network_manager.is_enabled():
            return False, "网络同步未启用"

        config = self.network_manager.get_config()
        server_url = config["server_url"]
        user_id = config["user_id"]
        machine_id = config["machine_id"]
        local_version = config.get("last_version", 0)
        local_config = load_config()
        if not local_config:
            return False, "本地配置为空"

        try:
            response = requests.post(
                f"{server_url.rstrip('/')}/api/config/push/{user_id}",
                json={
                    "config": local_config,
                    "local_version": local_version,
                    "machine_id": machine_id,
                },
                timeout=10,
            )
            if response.status_code != 200:
                message = f"服务器错误：HTTP {response.status_code}"
                self._report(message, log_callback)
                return False, message

            result = response.json()
            new_version = result.get("new_version", local_version)
            config["last_version"] = new_version
            self.network_manager.save_network_config(config)
            message = f"推送成功：新版本 {new_version}"
            self._report(message, log_callback)
            return True, message
        except requests.exceptions.ConnectionError:
            message = "无法连接到服务器"
            self._report(message, log_callback)
            return False, message
        except requests.RequestException as error:
            message = f"推送失败：{error}"
            self._report(message, log_callback)
            return False, message
        except ValueError as error:
            message = f"推送失败：{error}"
            self._report(message, log_callback)
            return False, message

    def sync_two_way(self, log_callback=None):
        """执行双向同步。"""
        if not self.network_manager.is_enabled():
            return False, "网络同步未启用"

        push_success, push_message = self.sync_push(log_callback)
        if not push_success:
            return False, f"推送失败：{push_message}"

        pull_success, pull_message = self.sync_pull(log_callback)
        if not pull_success:
            return False, f"拉取失败：{pull_message}"

        message = "双向同步完成"
        self._report(message, log_callback)
        return True, message
