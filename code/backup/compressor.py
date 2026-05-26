import os
import shutil
import time

from config.config_manager import load_config
from utils.logger import get_logger
from utils.paths import resolve_portable_path


_LOGGER = get_logger()


def compress_folder(source_folder: str, output_zip: str, timestamped: bool = False) -> str:
    """压缩指定目录并返回相对备份路径。"""
    if not os.path.isdir(source_folder):
        raise ValueError("指定的路径不是有效的文件夹")

    config = load_config()
    game_name = None
    for current_game_name, info in config.items():
        try:
            config_path = resolve_portable_path(info[1])
        except (IndexError, OSError, ValueError):
            continue
        if config_path == source_folder:
            game_name = current_game_name
            break

    if not game_name:
        game_name = os.path.basename(source_folder)

    game_dir = os.path.join(os.path.dirname(output_zip), game_name)
    os.makedirs(game_dir, exist_ok=True)

    folder_name = os.path.basename(source_folder)
    archive_name = folder_name if not timestamped else f"{folder_name}_{time.strftime('%Y%m%d_%H%M%S')}"
    output_path = os.path.join(game_dir, archive_name)

    if timestamped:
        base_output_path = output_path
        counter = 1
        while os.path.exists(output_path + ".zip"):
            output_path = f"{base_output_path}_{counter}"
            counter += 1

    shutil.make_archive(output_path, "zip", source_folder)
    _LOGGER.info(f"文件夹已成功压缩至 {output_path}.zip")
    return os.path.join(game_name, os.path.basename(output_path) + ".zip").replace("/", "\\")


def extract_zip(zip_path: str, extract_to: str | None = None) -> None:
    """解压 ZIP 文件。"""
    if not os.path.isfile(zip_path):
        raise ValueError("指定的路径不是有效的文件")

    target_dir = extract_to if extract_to is not None else os.path.splitext(zip_path)[0]
    shutil.unpack_archive(zip_path, target_dir)
    _LOGGER.info(f"文件已成功解压至 {target_dir}")

