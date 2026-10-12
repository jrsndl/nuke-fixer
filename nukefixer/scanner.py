"""Fast, cancellable, multi-threaded search for Nuke scripts (Qt-free).

Why it is faster than Path.rglob:
* os.scandir: on Windows the directory listing already carries type, size
  and mtime, so no extra stat call per file.
* Several folders are listed in parallel - on network shares the time is
  spent waiting for the server, not the CPU.
* Folders matching the exclude list (renders, plates, caches...) are never
  entered, which skips the thousands of image-sequence frames.
"""
import fnmatch
import logging
import os
import re
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from .paths import to_slash

log = logging.getLogger("nukefixer.scan")

IGNORE_CASE_DEFAULT = os.name == "nt"


class FoundFile(object):
    __slots__ = ("path", "folder", "name", "size", "mtime")

    def __init__(self, path, size=None, mtime=None):
        self.path = to_slash(path)
        self.folder, _, self.name = self.path.rpartition("/")
        self.size = size
        self.mtime = mtime

    def __repr__(self):
        return "FoundFile(%r)" % self.path


class ScanResult(object):
    def __init__(self):
        self.files = []
        self.dirs_scanned = 0
        self.errors = 0
        self.elapsed = 0.0
        self.cancelled = False


def compile_glob(pattern, ignore_case=IGNORE_CASE_DEFAULT):
    if not pattern or not pattern.strip():
        raise ValueError("The 'Search for' pattern is empty.")
    return re.compile(fnmatch.translate(pattern.strip()), re.IGNORECASE if ignore_case else 0)


def _is_link(entry):
    try:
        if entry.is_symlink():
            return True
        is_junction = getattr(entry, "is_junction", None)   # Python 3.12+
        return bool(is_junction and is_junction())
    except OSError:
        return True


def scan(root, pattern, contains="", excludes=(), threads=8, max_depth=0,
         cancel=None, progress=None, ignore_case=IGNORE_CASE_DEFAULT):
    """Search ``root`` recursively for files whose *name* matches ``pattern``.

    contains:  substring the full (forward-slash) path must contain.
    excludes:  glob patterns of folder *names* that are never entered.
    max_depth: 0 = unlimited, otherwise number of folder levels below root.
    cancel:    threading.Event; when set, the scan stops as soon as possible.
    progress:  callable(dirs_scanned, files_found), called from this thread.
    """
    result = ScanResult()
    if not root or not str(root).strip():
        raise ValueError("Choose a search root folder.")
    root = os.path.normpath(str(root).strip())
    if not os.path.isdir(root):
        raise ValueError("Search root does not exist: %s" % to_slash(root))

    flags = re.IGNORECASE if ignore_case else 0
    name_re = compile_glob(pattern, ignore_case)
    exclude_res = [re.compile(fnmatch.translate(p), flags) for p in excludes if p]
    needle = to_slash(contains or "")
    if ignore_case:
        needle = needle.lower()

    def list_dir(path, depth):
        files, subdirs = [], []
        try:
            with os.scandir(path) as it:
                for entry in it:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if _is_link(entry):
                                continue
                            if any(r.match(entry.name) for r in exclude_res):
                                continue
                            if max_depth <= 0 or depth < max_depth:
                                subdirs.append(entry.path)
                        elif name_re.match(entry.name):
                            full = to_slash(entry.path)
                            if needle and needle not in (full.lower() if ignore_case else full):
                                continue
                            st = entry.stat()
                            files.append(FoundFile(full, st.st_size, st.st_mtime))
                    except OSError:
                        continue
        except OSError as exc:
            log.debug("Cannot list %s: %s", path, exc)
            return files, subdirs, depth, True
        return files, subdirs, depth, False

    t0 = time.time()
    executor = ThreadPoolExecutor(max_workers=max(1, int(threads)))
    try:
        pending = {executor.submit(list_dir, root, 0)}
        while pending:
            if cancel is not None and cancel.is_set():
                for fut in pending:
                    fut.cancel()
                result.cancelled = True
                break
            done, pending = wait(pending, timeout=0.2, return_when=FIRST_COMPLETED)
            for fut in done:
                files, subdirs, depth, failed = fut.result()
                result.dirs_scanned += 1
                result.errors += int(failed)
                result.files.extend(files)
                for sub in subdirs:
                    pending.add(executor.submit(list_dir, sub, depth + 1))
            if progress is not None:
                progress(result.dirs_scanned, len(result.files))
    finally:
        executor.shutdown(wait=not result.cancelled)

    result.files.sort(key=lambda f: f.path.lower())
    result.elapsed = time.time() - t0
    return result
