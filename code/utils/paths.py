import os
import shutil
import sys
import threading
from pathlib import Path

from dotenv import load_dotenv, set_key


_PATH_LOCK = threading.RLock()
_ENV_LOADED = False
_DATA_MIGRATED = False


def get_project_root() -> Path:
    """获取项目根目录或打包后的运行目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def get_code_root() -> Path:
    """获取源码 code 目录。"""
    if getattr(sys, "frozen", False):
        return get_project_root()
    return get_project_root() / "code"


def _migrate_legacy_data_dir(target_dir: Path) -> None:
    """将历史上的根目录 data 迁移到 code/data。"""
    global _DATA_MIGRATED
    if _DATA_MIGRATED or getattr(sys, "frozen", False):
        return

    legacy_dir = get_project_root() / "data"
    if legacy_dir == target_dir or not legacy_dir.exists():
        _DATA_MIGRATED = True
        return

    for file_name in ("config.json", "network_config.json"):
        source_path = legacy_dir / file_name
        target_path = target_dir / file_name
        if not source_path.exists():
            continue
        if not target_path.exists() or source_path.stat().st_mtime >= target_path.stat().st_mtime:
            shutil.copy2(source_path, target_path)

    _DATA_MIGRATED = True


def get_data_dir() -> Path:
    """获取统一的数据目录。"""
    data_dir = get_project_root() / "data" if getattr(sys, "frozen", False) else get_code_root() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_data_dir(data_dir)
    return data_dir


def get_config_path() -> Path:
    """获取游戏配置文件路径。"""
    return get_data_dir() / "config.json"


def get_network_config_path() -> Path:
    """获取网络配置文件路径。"""
    return get_data_dir() / "network_config.json"


def get_log_file_path() -> Path:
    """获取日志文件路径。"""
    log_dir = get_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "gamesaveassistant.log"


def get_env_path() -> Path:
    """获取 .env 文件路径。"""
    return get_project_root() / ".env"


def get_current_username() -> str:
    """获取当前用户名。"""
    return os.environ.get("USERNAME") or os.path.basename(os.path.expanduser("~"))


def get_userprofile() -> str:
    """获取当前用户目录。"""
    return os.environ.get("USERPROFILE", os.path.expanduser("~"))


def _normalize_path_for_compare(path_text: str) -> str:
    """统一路径格式，便于比较。"""
    return os.path.normcase(os.path.normpath(path_text))


def to_portable_path(path_str: str) -> str:
    """将用户目录替换为占位符，便于跨机器同步。"""
    if not path_str:
        return path_str

    user_profile = get_userprofile()
    normalized_path = _normalize_path_for_compare(path_str)
    normalized_profile = _normalize_path_for_compare(user_profile)

    try:
        relative_path = os.path.relpath(normalized_path, normalized_profile)
        if relative_path.startswith(".."):
            return path_str.replace("/", "\\")
        if relative_path in (".", "", os.curdir):
            portable_path = "{USERPROFILE}"
        else:
            portable_path = "{USERPROFILE}\\" + relative_path
        return portable_path.replace("/", "\\")
    except ValueError:
        if normalized_path.startswith(normalized_profile):
            suffix = path_str[len(user_profile):]
            return ("{USERPROFILE}" + suffix).replace("/", "\\")
        return path_str.replace("/", "\\")


def resolve_portable_path(path_str: str) -> str:
    """将占位符路径解析为当前机器的真实路径。"""
    if not path_str:
        return path_str
    resolved = path_str.replace("{USERPROFILE}", get_userprofile()).replace("{USERNAME}", get_current_username())
    resolved = os.path.expandvars(resolved)
    resolved = os.path.expanduser(resolved)
    return resolved


def _ensure_env_loaded() -> None:
    """确保环境变量只加载一次。"""
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    env_path = get_env_path()
    default_backup_dir = Path(get_userprofile()) / "AppData" / "Local" / "Gamesavebackup"
    if not env_path.exists():
        env_path.write_text(f"BACKUP_DIR={default_backup_dir}\n", encoding="utf-8")
    load_dotenv(env_path)
    _ENV_LOADED = True


def get_backup_dir() -> str:
    """获取备份根目录。"""
    with _PATH_LOCK:
        _ensure_env_loaded()
        backup_dir = os.getenv("BACKUP_DIR", str(Path(get_userprofile()) / "AppData" / "Local" / "Gamesavebackup"))
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        return backup_dir


def set_backup_dir(new_path: str) -> str:
    """更新备份根目录。"""
    if not new_path:
        raise ValueError("备份目录不能为空")

    with _PATH_LOCK:
        backup_path = Path(new_path)
        backup_path.mkdir(parents=True, exist_ok=True)
        env_path = get_env_path()
        if not env_path.exists():
            env_path.write_text("", encoding="utf-8")
        set_key(str(env_path), "BACKUP_DIR", str(backup_path))
        os.environ["BACKUP_DIR"] = str(backup_path)
        return str(backup_path)


def get_backup_staging_dir() -> str:
    """获取备份暂存路径。"""
    return os.path.join(get_backup_dir(), "null")


def get_unzip_dir() -> str:
    """获取解压和总备份目录。"""
    return get_backup_dir()


def get_viewallprocesses_path() -> Path:
    """获取进程查看工具路径。"""
    if getattr(sys, "frozen", False):
        return get_project_root() / "Viewallprocesses.exe"
    return get_code_root() / "Viewallprocesses.exe"

