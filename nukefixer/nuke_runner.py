# -*- coding: utf-8 -*-
"""Executed INSIDE Nuke:  nuke -t nuke_runner.py <job.json>

Do not import this from the GUI. It must stay compatible with the Python
that ships with Nuke (2.7 for Nuke <= 12, 3.x for Nuke 13+).

One Nuke process handles several scripts (saves Nuke start-up time). For
each script it:
  1. stops early if the GUI created the job's stop file,
  2. makes a backup copy (never overwrites an existing backup),
  3. opens the script - a script that fails to load is NOT saved, so nodes
     from missing plugins can't be silently destroyed,
  4. runs the user's python script with ``nuke`` and ``nf`` available,
  5. saves (unless dry run or the user script set nf.skip_save = True),
  6. clears the script so the next one starts from a clean state.

Progress is reported as single lines on stdout ("NF_START {...}",
"NF_RESULT {...}", "NF_MSG {...}") and mirrored to a results file, so the
GUI still knows what happened if stdout is lost.
"""
from __future__ import print_function

import io
import json
import os
import runpy
import shutil
import sys
import time
import traceback

import nuke

try:
    text_type = unicode  # noqa: F821  (Python 2)
except NameError:
    text_type = str

_results_fh = None


def emit(tag, payload):
    line = tag + " " + json.dumps(payload)
    if not isinstance(line, text_type):
        line = line.decode("utf-8")
    try:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
    except Exception:
        pass
    if _results_fh is not None:
        try:
            _results_fh.write(line + u"\n")
            _results_fh.flush()
        except Exception:
            pass


class NFContext(object):
    """The ``nf`` object available to user scripts."""

    def __init__(self, path, dry_run):
        self.file = path
        self.dry_run = dry_run
        self.skip_save = False

    def log(self, message):
        emit("NF_MSG", {"file": self.file, "text": u"%s" % (message,)})


TMP_SUFFIX = ".nukefixer_tmp.nk"


def _read(path):
    with io.open(path, "rb") as fh:
        return fh.read()


def _path_variants(path):
    fwd = path.replace("\\", "/")
    return [fwd, fwd.replace("/", "\\")]


def save_script(path):
    """Save the open script into ``path`` via a temporary file.

    1. nuke.scriptSaveAs() writes a NEW file next to the original. Saving
       onto the file Nuke opened proved unreliable in nuke -t (it reported
       success but the changes never reached the file).
    2. Nuke stores the script's own path in the Root node, so the temp name
       is replaced by the real name inside the saved text.
    3. If the result is byte-identical to the original nothing changed, and
       the original is left alone.
    4. os.replace() renames the temp file over the original in one step.

    Returns (saved, message).
    """
    tmp = path + TMP_SUFFIX
    if os.path.exists(tmp):
        os.remove(tmp)
    original = _read(path)
    try:
        nuke.root().setModified(True)
    except Exception:
        pass
    nuke.scriptSaveAs(tmp, overwrite=1)
    if not os.path.isfile(tmp):
        raise RuntimeError("Nuke did not write the temporary file %s" % tmp)
    try:
        data = _read(tmp)
        for tmp_name, real_name in zip(_path_variants(tmp), _path_variants(path)):
            data = data.replace(tmp_name.encode("utf-8"), real_name.encode("utf-8"))
        if not data.strip():
            raise RuntimeError("Nuke wrote an empty file - original kept")
        if data == original:
            os.remove(tmp)
            return False, ("nothing saved - the script Nuke wrote is identical to the original "
                           "(no changes reached the script?)")
        with io.open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise
    return True, "saved (%d -> %d bytes)" % (len(original), len(data))


def process(path, job):
    dry_run = bool(job.get("dry_run"))
    if not os.path.isfile(path):
        raise IOError("File not found: %s" % path)

    backup = None
    if job.get("make_backup") and not dry_run:
        backup = path + job.get("backup_suffix", ".safecopy")
        if not os.path.exists(backup):
            shutil.copy2(path, backup)

    nuke.scriptOpen(path)

    ctx = NFContext(path, dry_run)
    init_globals = {"nuke": nuke, "nf": ctx, "NF_FILE": path}
    try:
        runpy.run_path(job["user_script"], init_globals=init_globals, run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (None, 0):
            raise RuntimeError("User script called sys.exit(%r)" % (exc.code,))

    if dry_run:
        return False, "dry run - not saved", None
    if ctx.skip_save:
        return False, "nothing to save (nf.skip_save)", backup
    saved, message = save_script(path)
    return saved, message, backup


def main(job_path):
    global _results_fh
    with io.open(job_path, "r", encoding="utf-8") as fh:
        job = json.load(fh)
    _results_fh = io.open(job["results_file"], "a", encoding="utf-8")

    script_dir = job.get("script_dir")
    if script_dir and os.path.isdir(script_dir) and script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    emit("NF_READY", {"pid": os.getpid(), "nuke": getattr(nuke, "NUKE_VERSION_STRING", "?")})
    stop_file = job.get("stop_file")
    for path in job["files"]:
        if stop_file and os.path.exists(stop_file):
            emit("NF_STOPPED", {})
            break
        emit("NF_START", {"file": path})
        t0 = time.time()
        ok, saved, backup = False, False, None
        try:
            saved, message, backup = process(path, job)
            ok = True
        except Exception:
            message = traceback.format_exc()
        finally:
            try:
                nuke.scriptClear()
            except Exception:
                pass
        emit("NF_RESULT", {"file": path, "ok": ok, "saved": saved, "backup": backup,
                           "message": message, "duration": time.time() - t0})
    _results_fh.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: nuke -t nuke_runner.py job.json")
        sys.exit(2)
    main(sys.argv[1])
