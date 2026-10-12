"""Queue items and saving / loading / exporting the queue (Qt-free)."""
import csv
import io
import json
import os
import time

from .paths import to_slash

PENDING = "pending"
RUNNING = "running"
DONE = "done"
FAILED = "failed"
STATUSES = (PENDING, RUNNING, DONE, FAILED)

FORMAT_ID = "nukefixer-queue"


class QueueItem(object):
    __slots__ = ("path", "enabled", "status", "message", "size", "mtime",
                 "duration", "finished_at", "saved", "backup")

    def __init__(self, path, enabled=True, status=PENDING, message="",
                 size=None, mtime=None, duration=None, finished_at=None, saved=None,
                 backup=None):
        self.path = to_slash(path)
        self.enabled = bool(enabled)
        self.status = status if status in STATUSES else PENDING
        self.message = message or ""
        self.size = size
        self.mtime = mtime
        self.duration = duration
        self.finished_at = finished_at
        self.saved = saved
        self.backup = to_slash(backup) if backup else None

    @property
    def folder(self):
        return self.path.rpartition("/")[0]

    @property
    def name(self):
        return self.path.rpartition("/")[2]

    @property
    def key(self):
        return path_key(self.path)

    def refresh_stat(self):
        try:
            st = os.stat(self.path)
            self.size, self.mtime = st.st_size, st.st_mtime
            return True
        except OSError:
            return False

    def to_dict(self):
        return {name: getattr(self, name) for name in self.__slots__}

    @classmethod
    def from_dict(cls, data):
        kwargs = {k: data.get(k) for k in cls.__slots__ if k in data}
        if not kwargs.get("path"):
            raise ValueError("queue item without path")
        item = cls(**kwargs)
        if item.status == RUNNING:          # interrupted run -> try again
            item.status = PENDING
        return item


def path_key(path):
    """Key used to de-duplicate queue entries (case-insensitive on Windows)."""
    key = to_slash(os.path.normpath(path))
    return key.lower() if os.name == "nt" else key


def save_queue(path, items):
    """Atomic write so a crash mid-save never corrupts the queue file."""
    data = {
        "format": FORMAT_ID,
        "version": 1,
        "saved": time.strftime("%Y-%m-%d %H:%M:%S"),
        "items": [item.to_dict() for item in items],
    }
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    os.replace(tmp, path)


def load_queue(path):
    """Load a queue saved by save_queue, or a plain text list of .nk paths."""
    with io.open(path, "r", encoding="utf-8-sig") as fh:
        text = fh.read()
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        data = json.loads(text)
        rows = data.get("items", []) if isinstance(data, dict) else data
        items = []
        for row in rows:
            if isinstance(row, str):
                items.append(QueueItem(row))
            else:
                items.append(QueueItem.from_dict(row))
        return items
    return [QueueItem(line.strip().strip('"')) for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")]


def export_csv(path, items):
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["path", "enabled", "status", "duration_s", "size", "modified", "message"])
        for it in items:
            writer.writerow([
                it.path, int(it.enabled), it.status,
                "" if it.duration is None else "%.1f" % it.duration,
                "" if it.size is None else it.size,
                "" if it.mtime is None else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(it.mtime)),
                (it.message or "").strip().splitlines()[-1] if it.message else "",
            ])


# ----------------------------------------------------------------- roll-back
RB_OK = "ok"                    # backup exists, file unchanged since NukeFixer saved it
RB_CHANGED = "changed"          # backup exists, but the file was modified after the run
RB_NO_BACKUP = "no_backup"
RB_NOT_DONE = "not_done"        # not processed (pending / failed) - nothing to roll back


def backup_path(item, suffix):
    """The backup the run reported, else <script><current suffix>."""
    return item.backup or (item.path + (suffix or ".safecopy"))


def plan_rollback(items, suffix, tolerance=2.0):
    """Classify items for roll-back. Returns a list of (item, backup, verdict).

    A file counts as "changed" when its modification time is newer than the
    one recorded right after NukeFixer saved it - someone has worked on it
    since, and rolling back would throw that work away.
    """
    plan = []
    for it in items:
        bak = backup_path(it, suffix)
        if it.status != DONE:
            verdict = RB_NOT_DONE
        elif not os.path.isfile(bak):
            verdict = RB_NO_BACKUP
        else:
            verdict = RB_OK
            try:
                current = os.stat(it.path).st_mtime
                if it.mtime is not None and current > it.mtime + tolerance:
                    verdict = RB_CHANGED
            except OSError:
                pass            # script itself missing: restoring the backup is fine
        plan.append((it, bak, verdict))
    return plan


def rollback_file(path, backup):
    """Replace ``path`` with ``backup`` (the backup takes the original name).

    os.replace does the delete + rename in one step, so there is never a
    moment when neither file exists. Returns (ok, message).
    """
    if not os.path.isfile(backup):
        return False, "backup not found: %s" % backup
    try:
        os.replace(backup, path)
    except OSError as exc:
        return False, "roll-back failed (file open in Nuke or read-only?): %s" % exc
    return True, "rolled back from %s" % os.path.basename(backup)


def human_size(num):
    if num is None:
        return ""
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return ("%d %s" % (num, unit)) if unit == "B" else ("%.1f %s" % (num, unit))
        num /= 1024.0
    return ""


def human_time(seconds):
    if seconds is None:
        return ""
    seconds = int(round(max(0, seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return "%d:%02d:%02d" % (h, m, s) if h else "%d:%02d" % (m, s)
