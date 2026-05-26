import psutil


def iter_exe_processes():
    """遍历当前所有 exe 进程。"""
    for process in psutil.process_iter(["name", "pid", "exe"]):
        try:
            name = process.info.get("name") or ""
            if name.lower().endswith(".exe"):
                yield {
                    "name": name,
                    "pid": process.info.get("pid", 0),
                    "exe": process.info.get("exe") or "",
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue


def find_process_by_name(process_name: str):
    """按名称查找进程。"""
    if not process_name:
        return None

    target_name = process_name.lower()
    for process_info in iter_exe_processes():
        if (process_info.get("name") or "").lower() == target_name:
            return process_info
    return None

