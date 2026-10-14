import os
import shutil
import sys
from typing import List, Optional


def extra_bin_dirs() -> List[str]:
    dirs = []
    if sys.platform == "darwin":
        dirs.extend(["/opt/homebrew/bin", "/usr/local/bin"])
    elif sys.platform == "win32":
        dirs.extend(
            [
                r"C:\ffmpeg\bin",
                os.path.join(os.environ.get("USERPROFILE") or "", "ffmpeg", "bin"),
            ]
        )
    else:
        dirs.extend(["/usr/bin", "/usr/local/bin"])
    return [d for d in dirs if d and os.path.isdir(d)]


def ensure_ffmpeg_on_path() -> None:
    """Put common FFmpeg install locations on PATH so subprocess can find them."""
    current = os.environ.get("PATH", "")
    parts = current.split(os.pathsep) if current else []
    prepend = [d for d in extra_bin_dirs() if d not in parts]
    if prepend:
        os.environ["PATH"] = os.pathsep.join(prepend + parts)


def find_tool(name: str) -> Optional[str]:
    ensure_ffmpeg_on_path()
    found = shutil.which(name)
    if found:
        return found
    suffix = ".exe" if sys.platform == "win32" and not name.endswith(".exe") else ""
    for folder in extra_bin_dirs():
        candidate = os.path.join(folder, name + suffix)
        if os.path.isfile(candidate):
            return candidate
    return None


def install_hint() -> str:
    """User-facing install steps. The agent must relay this and not install unless asked."""
    if sys.platform == "darwin":
        return (
            "未找到 ffmpeg。请在终端执行：\n"
            "brew install ffmpeg\n"
            "如果还没有 Homebrew，先打开 https://brew.sh 按页面上的命令安装，再执行上面这句。\n"
            "装完后执行 ffmpeg -version，能打出版本号即可。"
        )
    if sys.platform == "win32":
        return (
            "未找到 ffmpeg。请在 PowerShell 执行：\n"
            "winget install Gyan.FFmpeg\n"
            "装完后新开一个终端，执行 ffmpeg -version，能打出版本号即可。"
        )
    return (
        "未找到 ffmpeg。请用系统包管理器安装 ffmpeg，并把它加入 PATH。\n"
        "装完后执行 ffmpeg -version，能打出版本号即可。"
    )


def require_ffmpeg() -> str:
    path = find_tool("ffmpeg")
    if not path:
        raise FileNotFoundError(install_hint())
    return path


def require_ffprobe() -> str:
    path = find_tool("ffprobe")
    if not path:
        raise FileNotFoundError(install_hint())
    return path
