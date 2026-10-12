"""Small shared GUI helpers."""
import os
import subprocess
import sys

from .qt import QtCore, QtGui, QtWidgets, QShortcut, Qt
from .models import PATH_ROLE


def reveal_in_file_manager(path):
    """Open the file manager with ``path`` selected (or its folder opened)."""
    path = os.path.normpath(path)
    if not os.path.exists(path):
        path = os.path.dirname(path)
        if not os.path.exists(path):
            return False
    try:
        if sys.platform.startswith("win"):
            if os.path.isfile(path):
                subprocess.Popen('explorer /select,"%s"' % path)
            else:
                os.startfile(path)  # noqa - Windows only
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        else:
            folder = path if os.path.isdir(path) else os.path.dirname(path)
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))
    except OSError:
        return False
    return True


NUKE_INSTANCES_WITHOUT_WARNING = 5


def open_in_nuke(parent, settings, paths):
    """Open each script in its own interactive Nuke. Asks first above 5."""
    import logging
    from .runner import launch_gui
    log = logging.getLogger("nukefixer")
    paths = list(dict.fromkeys(p for p in paths if p))
    if not paths:
        return 0
    exe = (settings.get("nuke_executable") or "").strip()
    if not exe or not os.path.isfile(exe):
        QtWidgets.QMessageBox.critical(parent, "Open in Nuke", "Nuke executable not found:\n  %s\n"
                                       "Set it on the Settings tab." % (exe or "(empty)"))
        return 0
    missing = [p for p in paths if not os.path.isfile(p)]
    paths = [p for p in paths if os.path.isfile(p)]
    if missing:
        log.warning("Open in Nuke: %d file(s) not found:\n%s", len(missing), "\n".join(missing))
    if not paths:
        QtWidgets.QMessageBox.warning(parent, "Open in Nuke", "The selected file(s) don't exist.")
        return 0
    if len(paths) > NUKE_INSTANCES_WITHOUT_WARNING:
        answer = QtWidgets.QMessageBox.warning(
            parent, "Open in Nuke",
            "This starts %d separate Nuke sessions, one per script.\n\n"
            "Each one takes an interactive licence and several GB of RAM.\n\nOpen all %d?"
            % (len(paths), len(paths)),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)
        if answer != QtWidgets.QMessageBox.Yes:
            return 0
    opened = 0
    for p in paths:
        try:
            launch_gui(exe, p, settings.get("nuke_gui_args"))
            opened += 1
            log.info("Opened in Nuke: %s", p)
        except OSError as exc:
            log.error("Cannot start Nuke for %s: %s", p, exc)
            QtWidgets.QMessageBox.critical(parent, "Open in Nuke", "Cannot start Nuke:\n%s" % exc)
            break
    return opened


def setup_table(view, proxy):
    view.setModel(proxy)
    view.setSortingEnabled(True)
    view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
    view.setAlternatingRowColors(True)
    view.setWordWrap(False)
    view.setShowGrid(False)
    view.verticalHeader().setVisible(False)
    view.verticalHeader().setDefaultSectionSize(22)
    header = view.horizontalHeader()
    header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
    header.setStretchLastSection(True)
    header.setHighlightSections(False)
    header.setResizeContentsPrecision(200)   # don't measure 10k rows on resize
    view.setColumnWidth(0, 28)
    view.setContextMenuPolicy(Qt.CustomContextMenu)
    view.sortByColumn(-1, Qt.AscendingOrder)


def selected_source_rows(view, proxy):
    rows = {proxy.mapToSource(ix).row() for ix in view.selectionModel().selectedRows()}
    return sorted(r for r in rows if r >= 0)


def visible_source_rows(proxy):
    return [proxy.mapToSource(proxy.index(r, 0)).row() for r in range(proxy.rowCount())]


def selected_paths(view, proxy):
    return [ix.data(PATH_ROLE) for ix in view.selectionModel().selectedRows()]


def add_shortcut(widget, key, slot):
    sc = QShortcut(QtGui.QKeySequence(key), widget)
    sc.setContext(Qt.WidgetShortcut)
    sc.activated.connect(slot)
    return sc


def hint_label(text):
    label = QtWidgets.QLabel(text)
    label.setObjectName("hint")
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return label


def set_invalid(widget, invalid):
    widget.setProperty("invalid", "true" if invalid else "false")
    widget.style().unpolish(widget)
    widget.style().polish(widget)
