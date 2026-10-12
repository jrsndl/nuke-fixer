"""Logging setup and the Log tab (level / text / source filtering)."""
import html
import logging
import logging.handlers
import os
import time
from collections import deque

from .qt import QtCore, QtGui, QtWidgets, Signal
from .config import LOG_LEVELS

ROOT_LOGGER = "nukefixer"
NUKE_LOGGER = "nukefixer.nuke"
FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"

LEVEL_COLORS = {
    logging.DEBUG: "#7f7f7f",
    logging.INFO: "#c8c8c8",
    logging.WARNING: "#ffa02f",
    logging.ERROR: "#ff6b6b",
    logging.CRITICAL: "#ff3b3b",
}

_file_handler = None


def setup_logging(log_file, file_level="INFO", max_kb=5000):
    """Rotating file log + the root 'nukefixer' logger. Safe to call again."""
    global _file_handler
    root = logging.getLogger(ROOT_LOGGER)
    root.setLevel(logging.DEBUG)
    root.propagate = False
    if _file_handler is not None:
        root.removeHandler(_file_handler)
        _file_handler.close()
        _file_handler = None
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        _file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max(100, int(max_kb)) * 1024, backupCount=3, encoding="utf-8")
        _file_handler.setFormatter(logging.Formatter(FORMAT))
        _file_handler.setLevel(getattr(logging, file_level, logging.INFO))
        root.addHandler(_file_handler)
    except OSError as exc:
        root.warning("Cannot write log file %s: %s", log_file, exc)
    return root


def set_file_level(level_name):
    if _file_handler is not None:
        _file_handler.setLevel(getattr(logging, level_name, logging.INFO))


class _Emitter(QtCore.QObject):
    record = Signal(object)


class QtLogHandler(logging.Handler):
    """Thread-safe: records are delivered to the GUI thread through a signal."""

    def __init__(self):
        super(QtLogHandler, self).__init__(logging.DEBUG)
        self.emitter = _Emitter()

    def emit(self, record):
        try:
            record.formatted_message = record.getMessage()
            self.emitter.record.emit(record)
        except RuntimeError:     # Qt object already deleted at shutdown
            pass


class LogTab(QtWidgets.QWidget):
    MAX_RECORDS = 50000
    MAX_SHOWN = 20000

    levelChanged = Signal(str)
    nukeOutputChanged = Signal(bool)

    def __init__(self, log_file, level="INFO", show_nuke=False, parent=None):
        super(LogTab, self).__init__(parent)
        self.log_file = log_file
        self.records = deque(maxlen=self.MAX_RECORDS)
        self._pending = []
        self.handler = QtLogHandler()
        self.handler.emitter.record.connect(self._on_record)
        logging.getLogger(ROOT_LOGGER).addHandler(self.handler)

        self.level = QtWidgets.QComboBox()
        self.level.addItems(LOG_LEVELS)
        self.level.setCurrentText(level if level in LOG_LEVELS else "INFO")
        self.level.setToolTip("Show messages of this level and above")
        self.text_filter = QtWidgets.QLineEdit()
        self.text_filter.setPlaceholderText("Filter text...")
        self.text_filter.setClearButtonEnabled(True)
        self.show_nuke = QtWidgets.QCheckBox("Nuke output")
        self.show_nuke.setToolTip("Show the raw output of the Nuke processes (logged at DEBUG level)")
        self.show_nuke.setChecked(show_nuke)
        self.autoscroll = QtWidgets.QCheckBox("Auto-scroll")
        self.autoscroll.setChecked(True)
        clear = QtWidgets.QPushButton("Clear")
        save = QtWidgets.QPushButton("Save...")
        open_file = QtWidgets.QPushButton("Open Log File")

        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("Verbosity:"))
        top.addWidget(self.level)
        top.addWidget(self.text_filter, 1)
        top.addWidget(self.show_nuke)
        top.addWidget(self.autoscroll)
        top.addWidget(clear)
        top.addWidget(save)
        top.addWidget(open_file)

        self.view = QtWidgets.QPlainTextEdit()
        self.view.setReadOnly(True)
        self.view.setMaximumBlockCount(self.MAX_SHOWN)
        self.view.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.view.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.view)

        self._refilter_timer = QtCore.QTimer(self, singleShot=True, interval=250)
        self._refilter_timer.timeout.connect(self.rebuild)
        self._flush_timer = QtCore.QTimer(self, interval=200)
        self._flush_timer.timeout.connect(self._flush)
        self._flush_timer.start()

        self.level.currentTextChanged.connect(self._on_level)
        self.text_filter.textChanged.connect(lambda _t: self._refilter_timer.start())
        self.show_nuke.toggled.connect(self._on_show_nuke)
        clear.clicked.connect(self.clear)
        save.clicked.connect(self.save)
        open_file.clicked.connect(self.open_log_file)

    # ------------------------------------------------------------ records
    def _on_record(self, record):
        self.records.append(record)
        self._pending.append(record)

    def _accept(self, record, min_level, needle, show_nuke):
        if record.levelno < min_level:
            return False
        if not show_nuke and record.name.startswith(NUKE_LOGGER):
            return False
        if needle and needle not in record.formatted_message.lower():
            return False
        return True

    def _filter_args(self):
        return (getattr(logging, self.level.currentText(), logging.INFO),
                self.text_filter.text().strip().lower(),
                self.show_nuke.isChecked())

    @staticmethod
    def _html(record):
        ts = time.strftime("%H:%M:%S", time.localtime(record.created))
        color = LEVEL_COLORS.get(record.levelno, "#c8c8c8")
        msg = html.escape(record.formatted_message).replace("  ", "&nbsp; ").replace("\n", "<br>")
        source = "nuke" if record.name.startswith(NUKE_LOGGER) else record.levelname
        return '<span style="color:%s">%s %-7s %s</span>' % (color, ts, source, msg)

    def _append(self, records):
        if not records:
            return
        bar = self.view.verticalScrollBar()
        at_bottom = bar.value() >= bar.maximum() - 4
        for rec in records[-self.MAX_SHOWN:]:
            self.view.appendHtml(self._html(rec))
        if self.autoscroll.isChecked() and at_bottom:
            bar.setValue(bar.maximum())

    def _flush(self):
        if not self._pending:
            return
        pending, self._pending = self._pending, []
        args = self._filter_args()
        self._append([r for r in pending if self._accept(r, *args)])

    def rebuild(self):
        self._pending = []
        self.view.clear()
        args = self._filter_args()
        self._append([r for r in self.records if self._accept(r, *args)])
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().maximum())

    # ------------------------------------------------------------ actions
    def _on_level(self, text):
        self.rebuild()
        self.levelChanged.emit(text)

    def _on_show_nuke(self, on):
        self.rebuild()
        self.nukeOutputChanged.emit(on)

    def clear(self):
        self.records.clear()
        self._pending = []
        self.view.clear()

    def save(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Log", "nukefixer_log.txt", "Text files (*.txt *.log);;All files (*)")
        if not path:
            return
        fmt = logging.Formatter(FORMAT)
        with open(path, "w", encoding="utf-8") as fh:
            args = self._filter_args()
            for rec in self.records:
                if self._accept(rec, *args):
                    fh.write(fmt.format(rec) + "\n")

    def open_log_file(self):
        if os.path.exists(self.log_file):
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(self.log_file))

    def shutdown(self):
        logging.getLogger(ROOT_LOGGER).removeHandler(self.handler)
