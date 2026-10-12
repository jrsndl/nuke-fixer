"""Settings defaults and robust value coercion (Qt-free).

The GUI persists these through QSettings (settings.ini). Values read back from
an ini file can be strings ('true', '0', '2'), lists (unquoted commas) or
missing - everything goes through ``coerce`` so a bad value falls back to the
default for that key instead of resetting the whole file.
"""
import glob
import os
import re
import sys
from collections import OrderedDict

VERSION_MODES = ("first", "last", "all")
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")

DEFAULT_EXCLUDES = ".*, __pycache__, renders, render, plates, plate, elements, cache, _cache, tmp, dailies"

DEFAULT_SCRIPT = '''"""Runs once for every Nuke script in the queue, after it has been opened.

Available names:
    nuke  - the Nuke module
    nf    - nf.file (path), nf.dry_run, nf.skip_save, nf.log("message")

Raise an exception to mark the script as failed - it will NOT be saved.
Set nf.skip_save = True when nothing needed changing.
"""
import nuke

changed = 0
for node in nuke.allNodes(recurseGroups=True):
    pass  # modify nodes here, count what you changed

if not changed:
    nf.skip_save = True
nf.log("changed %d node(s)" % changed)
'''


def _default_nuke():
    found = detect_nuke_executables()
    if found:
        return found[0]
    if sys.platform.startswith("win"):
        return "C:/Program Files/Nuke13.2v4/Nuke13.2.exe"
    return ""


DEFAULTS = OrderedDict([
    # --- Find Nuke Scripts tab
    ("search_start", ""),
    ("only_if_contains", "/work/comp/"),
    ("search_for", "*_comp_v???.nk"),
    ("version_regex", r"_v(\d+)\.nk$"),
    ("version_mode", "last"),
    # --- Python Script tab
    ("python_script", DEFAULT_SCRIPT),
    ("python_script_path", ""),
    # --- Nuke / processing
    ("nuke_executable", None),          # resolved lazily by _default_nuke()
    ("interactive_license", False),     # False: -t (nuke_r), True: -ti (nuke_i)
    ("nuke_extra_args", ""),
    ("nuke_gui_args", ""),              # used by "Open in Nuke"
    ("max_processes", 2),
    ("files_per_process", 10),
    ("timeout_per_file", 600),          # seconds, 0 = no limit
    ("startup_timeout", 300),           # seconds without any progress
    ("hide_console", True),
    # --- safety
    ("make_backup", True),
    ("backup_suffix", ".safecopy"),
    ("dry_run", False),
    # --- search
    ("scan_excludes", DEFAULT_EXCLUDES),
    ("scan_threads", 8),
    ("scan_max_depth", 0),              # 0 = unlimited
    ("search_delay_ms", 600),
    # --- queue / logging
    ("restore_queue", True),
    ("log_level_file", "INFO"),
    ("log_level_view", "INFO"),
    ("log_show_nuke_output", False),
    ("log_max_kb", 5000),
    # --- window state
    ("window_geometry", ""),
    ("current_tab", 0),
    ("last_queue_dir", ""),
])


def default(key):
    value = DEFAULTS[key]
    if key == "nuke_executable" and value is None:
        return _default_nuke()
    return value


def to_bool(raw, fallback=False):
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return fallback
    if isinstance(raw, (int, float)):
        return bool(raw)
    text = str(raw).strip().lower()
    if text in ("1", "true", "yes", "on", "y"):
        return True
    if text in ("0", "false", "no", "off", "n", ""):
        return False
    return fallback


def coerce(raw, fallback):
    """Convert a raw QSettings value to the type of ``fallback``."""
    if raw is None:
        return fallback
    if isinstance(raw, (list, tuple)):
        raw = ", ".join(str(x) for x in raw)
    if isinstance(fallback, bool):
        return to_bool(raw, fallback)
    if isinstance(fallback, int):
        try:
            return int(float(str(raw).strip()))
        except (TypeError, ValueError):
            return fallback
    if isinstance(fallback, float):
        try:
            return float(str(raw).strip())
        except (TypeError, ValueError):
            return fallback
    return str(raw)


def legacy_version_mode(first, last, all_):
    """Map the old apply_first/apply_last/apply_all radio values."""
    if to_bool(first):
        return "first"
    if to_bool(all_):
        return "all"
    if to_bool(last):
        return "last"
    return None


def parse_list(text):
    """'a, b; c' -> ['a', 'b', 'c']"""
    return [p.strip() for p in re.split(r"[,;\n]", text or "") if p.strip()]


def _version_tuple(path):
    nums = re.findall(r"\d+", os.path.basename(os.path.dirname(path)) + os.path.basename(path))
    return tuple(int(n) for n in nums)


def detect_nuke_executables():
    """Find installed Nuke executables, newest first."""
    if sys.platform.startswith("win"):
        roots = [os.environ.get("ProgramFiles", "C:/Program Files")]
        patterns = ["Nuke*/Nuke*.exe"]
    elif sys.platform == "darwin":
        roots = ["/Applications"]
        patterns = ["Nuke*/Nuke*.app/Contents/MacOS/Nuke*"]
    else:
        roots = ["/usr/local", "/opt"]
        patterns = ["Nuke*/Nuke*"]
    name_re = re.compile(r"^Nuke\d+\.\d+(v\d+)?(\.exe)?$", re.IGNORECASE)
    found = []
    for root in roots:
        for pattern in patterns:
            for path in glob.glob(os.path.join(root, pattern)):
                if os.path.isfile(path) and name_re.match(os.path.basename(path)):
                    found.append(path.replace("\\", "/"))
    return sorted(set(found), key=_version_tuple, reverse=True)
