"""Table models for the search results and the queue (model/view, no per-row widgets)."""
import time

from .qt import QtCore, QtGui, Qt, Signal, is_checked
from . import queue_io
from .versions import version_key
from .queue_io import DONE, FAILED, PENDING, RUNNING, QueueItem, human_size, human_time, path_key

SORT_ROLE = Qt.UserRole + 1
PATH_ROLE = Qt.UserRole + 2

STATUS_TEXT = {PENDING: "Pending", RUNNING: "Running", DONE: "Done", FAILED: "Failed"}
STATUS_BG = {RUNNING: QtGui.QColor("sienna"), DONE: QtGui.QColor("darkgreen"), FAILED: QtGui.QColor("maroon")}


def fmt_time(mtime):
    if not mtime:
        return ""
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))


def make_proxy(model, parent=None):
    proxy = QtCore.QSortFilterProxyModel(parent)
    proxy.setSourceModel(model)
    proxy.setSortRole(SORT_ROLE)
    proxy.setFilterKeyColumn(-1)
    proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
    proxy.setDynamicSortFilter(False)
    return proxy


class _CheckableModel(QtCore.QAbstractTableModel):
    """Common bits: column 0 is a checkbox, headers, sort role."""
    COLUMNS = ()
    countsChanged = Signal()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else len(self.COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and 0 <= section < len(self.COLUMNS):
            return self.COLUMNS[section]
        return None

    def _emit_rows(self, rows, first_col=0, last_col=None):
        if not rows:
            return
        last_col = len(self.COLUMNS) - 1 if last_col is None else last_col
        self.dataChanged.emit(self.index(min(rows), first_col), self.index(max(rows), last_col))


class ResultsModel(_CheckableModel):
    COLUMNS = ("", "File", "Version", "Folder", "Modified", "Size", "In queue")

    def __init__(self, parent=None):
        super(ResultsModel, self).__init__(parent)
        self._rows = []          # [candidate, checked]
        self._queued = set()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def set_candidates(self, candidates, checked=True):
        self.beginResetModel()
        self._rows = [[c, checked] for c in candidates]
        self.endResetModel()
        self.countsChanged.emit()

    def set_queued_keys(self, keys):
        self._queued = keys
        if self._rows:
            self._emit_rows([0, len(self._rows) - 1], 6, 6)

    def candidates(self, checked_only=False):
        return [c for c, chk in self._rows if chk or not checked_only]

    def candidate(self, row):
        return self._rows[row][0]

    def is_row_checked(self, row):
        return self._rows[row][1]

    def checked_count(self):
        return sum(1 for _, chk in self._rows if chk)

    def set_checked(self, rows, checked):
        for r in rows:
            self._rows[r][1] = checked
        self._emit_rows(list(rows), 0, 0)
        self.countsChanged.emit()

    def set_all_checked(self, checked):
        self.set_checked(range(len(self._rows)), checked)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 0:
            f |= Qt.ItemIsUserCheckable
        return f

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        cand, checked = self._rows[index.row()]
        f, col = cand.file, index.column()
        if role == Qt.CheckStateRole and col == 0:
            return Qt.Checked if checked else Qt.Unchecked
        if role == PATH_ROLE:
            return f.path
        queued = path_key(f.path) in self._queued
        if role == Qt.DisplayRole:
            return ("", f.name, cand.version, f.folder, fmt_time(f.mtime),
                    human_size(f.size), "✓" if queued else "")[col]
        if role == SORT_ROLE:
            vk = version_key(cand.version)
            vsort = "0:%015d" % vk[1] if vk[0] == 0 else "1:" + vk[2]
            return (int(checked), f.name.lower(), vsort, f.folder.lower(),
                    f.mtime or 0, f.size or 0, int(queued))[col]
        if role == Qt.ToolTipRole:
            return f.path
        if role == Qt.TextAlignmentRole and col in (2, 5, 6):
            return int(Qt.AlignRight | Qt.AlignVCenter) if col == 5 else int(Qt.AlignCenter)
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and index.column() == 0 and role == Qt.CheckStateRole:
            self._rows[index.row()][1] = is_checked(value)
            self.dataChanged.emit(index, index)
            self.countsChanged.emit()
            return True
        return False


class QueueModel(_CheckableModel):
    COLUMNS = ("", "Status", "File", "Folder", "Modified", "Size", "Time", "Message")

    def __init__(self, parent=None):
        super(QueueModel, self).__init__(parent)
        self.items = []
        self._index = {}
        self.locked = False

    # ---------------------------------------------------------- structure
    def rowCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else len(self.items)

    def _reindex(self):
        self._index = {it.key: row for row, it in enumerate(self.items)}

    def keys(self):
        return set(self._index)

    def set_items(self, items):
        self.beginResetModel()
        seen, unique = set(), []
        for it in items:
            if it.key not in seen:
                seen.add(it.key)
                unique.append(it)
        self.items = unique
        self._reindex()
        self.endResetModel()
        self.countsChanged.emit()

    def add_files(self, found_files):
        """Add FoundFile objects; returns (added, already_in_queue)."""
        new = []
        keys = set(self._index)
        for f in found_files:
            k = path_key(f.path)
            if k in keys:
                continue
            keys.add(k)
            new.append(QueueItem(f.path, size=f.size, mtime=f.mtime))
        if new:
            first = len(self.items)
            self.beginInsertRows(QtCore.QModelIndex(), first, first + len(new) - 1)
            self.items.extend(new)
            self._reindex()
            self.endInsertRows()
            self.countsChanged.emit()
        return len(new), len(found_files) - len(new)

    def remove_rows(self, rows):
        rows = sorted(set(rows), reverse=True)
        if not rows:
            return
        self.beginResetModel()
        for r in rows:
            del self.items[r]
        self._reindex()
        self.endResetModel()
        self.countsChanged.emit()

    def remove_where(self, predicate):
        self.remove_rows([r for r, it in enumerate(self.items) if predicate(it)])

    # -------------------------------------------------------------- state
    def item(self, row):
        return self.items[row]

    def row_for_path(self, path):
        return self._index.get(path_key(path))

    def item_for_path(self, path):
        row = self.row_for_path(path)
        return None if row is None else self.items[row]

    def item_changed(self, path):
        row = self.row_for_path(path)
        if row is not None:
            self._emit_rows([row])
        self.countsChanged.emit()

    def set_locked(self, locked):
        self.locked = locked
        if self.items:
            self._emit_rows([0, len(self.items) - 1], 0, 0)

    def set_enabled(self, rows, enabled):
        for r in rows:
            self.items[r].enabled = enabled
        self._emit_rows(list(rows), 0, 0)
        self.countsChanged.emit()

    def set_status(self, rows, status):
        for r in rows:
            it = self.items[r]
            it.status, it.message, it.duration, it.saved = status, "", None, None
        self._emit_rows(list(rows))
        self.countsChanged.emit()

    def runnable(self):
        return [it for it in self.items if it.enabled and it.status == PENDING]

    def counts(self):
        c = {PENDING: 0, RUNNING: 0, DONE: 0, FAILED: 0, "disabled": 0, "total": len(self.items)}
        for it in self.items:
            c[it.status] += 1
            if not it.enabled:
                c["disabled"] += 1
        c["runnable"] = sum(1 for it in self.items if it.enabled and it.status == PENDING)
        return c

    # ------------------------------------------------------------ Qt API
    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 0 and not self.locked:
            f |= Qt.ItemIsUserCheckable
        return f

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        it, col = self.items[index.row()], index.column()
        if role == Qt.CheckStateRole and col == 0:
            return Qt.Checked if it.enabled else Qt.Unchecked
        if role == PATH_ROLE:
            return it.path
        first_line = (it.message or "").strip().splitlines()
        short_msg = first_line[-1] if first_line else ""
        if role == Qt.DisplayRole:
            status = STATUS_TEXT.get(it.status, it.status)
            if it.status == DONE and it.saved is False:
                status = "Done (not saved)"
            return ("", status, it.name, it.folder, fmt_time(it.mtime), human_size(it.size),
                    human_time(it.duration), short_msg)[col]
        if role == SORT_ROLE:
            return (int(it.enabled), queue_io.STATUSES.index(it.status), it.name.lower(),
                    it.folder.lower(), it.mtime or 0, it.size or 0, it.duration or 0,
                    short_msg.lower())[col]
        if role == Qt.BackgroundRole and col == 1 and it.status in STATUS_BG:
            return QtGui.QBrush(STATUS_BG[it.status])
        if role == Qt.ForegroundRole:
            if not it.enabled:
                return QtGui.QBrush(QtGui.QColor("#6a6a6a"))
            if col == 1 and it.status in STATUS_BG:
                return QtGui.QBrush(QtGui.QColor("white"))
        if role == Qt.ToolTipRole:
            if col == 7 and it.message:
                return it.message if len(it.message) < 4000 else it.message[-4000:]
            return it.path
        if role == Qt.TextAlignmentRole and col in (5, 6):
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and index.column() == 0 and role == Qt.CheckStateRole and not self.locked:
            self.items[index.row()].enabled = is_checked(value)
            self.dataChanged.emit(index, index.sibling(index.row(), len(self.COLUMNS) - 1))
            self.countsChanged.emit()
            return True
        return False
