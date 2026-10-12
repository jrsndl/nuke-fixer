"""Where things live: app dir, bundled resources, user data (settings, logs)."""
import os
import shutil
import sys

from . import APP_NAME


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def to_slash(path):
    """Normalise a path to forward slashes (what Nuke and the UI use)."""
    return str(path).replace("\\", "/")


def app_dir():
    """Folder of the executable (frozen) or the repository root (source)."""
    if is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_dir():
    """Folder holding bundled read-only resources (PyInstaller's _MEIPASS)."""
    if is_frozen():
        return getattr(sys, "_MEIPASS", app_dir())
    return app_dir()


def resource(*parts):
    return os.path.join(resource_dir(), *parts)


def runner_script():
    """Path of the script Nuke executes. Must be a real file on disk."""
    return resource("nukefixer", "nuke_runner.py")


def images_dir():
    return resource("images")


def scripts_dir():
    """Folder with example / user python scripts (starting point of Load...)."""
    for base in (app_dir(), resource_dir()):
        candidate = os.path.join(base, "scripts")
        if os.path.isdir(candidate):
            return candidate
    return app_dir()


def _platform_user_dir():
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, APP_NAME)


def _writable(folder):
    return os.path.isdir(folder) and os.access(folder, os.W_OK)


def user_data_dir():
    """Settings, logs and the autosaved queue.

    Running from source keeps the old behaviour (files next to the code) as
    long as that folder is writable; a frozen build, or a read-only install,
    uses the per-user application data folder.
    """
    if not is_frozen() and _writable(app_dir()):
        return app_dir()
    folder = _platform_user_dir()
    os.makedirs(folder, exist_ok=True)
    return folder


def settings_path():
    path = os.path.join(user_data_dir(), "settings.ini")
    legacy = os.path.join(app_dir(), "settings.ini")
    # One-time migration of a settings.ini that sat next to the old exe.
    if not os.path.exists(path) and os.path.isfile(legacy) and legacy != path:
        try:
            shutil.copy2(legacy, path)
        except OSError:
            pass
    return path


def log_path():
    return os.path.join(user_data_dir(), "NukeFixer.log")


def autosave_queue_path():
    return os.path.join(user_data_dir(), "last_queue.json")
