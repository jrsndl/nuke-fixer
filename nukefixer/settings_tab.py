"""'Settings' tab: Nuke executable, processing, safety, search and logging."""
import os

from .qt import QtCore, QtGui, QtWidgets, Qt, qexec
from . import config
from .paths import log_path, to_slash
from .widgets import hint_label, set_invalid


class SettingsTab(QtWidgets.QWidget):
    def __init__(self, settings, parent=None):
        super(SettingsTab, self).__init__(parent)
        self.settings = settings
        self._widgets = {}

        content = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(content)

        # --- Nuke
        g = self._group(lay, "Nuke")
        exe = self._line("nuke_executable")
        browse = QtWidgets.QPushButton("Browse...")
        detect = QtWidgets.QPushButton("Detect")
        detect.setToolTip("Look for installed Nuke versions")
        row = QtWidgets.QHBoxLayout()
        row.addWidget(exe, 1)
        row.addWidget(browse)
        row.addWidget(detect)
        g.addRow("Nuke executable:", row)
        g.addRow("", self._check("interactive_license", "Use interactive licence (-ti instead of -t)",
                                 "-t uses a render licence (nuke_r), which most studios have more of. "
                                 "Only enable if your scripts need interactive features."))
        g.addRow("Extra Nuke arguments:", self._line("nuke_extra_args",
                 "Added after -t / -ti, e.g. --nukex   (quote paths that contain spaces)"))
        g.addRow("Open in Nuke arguments:", self._line("nuke_gui_args",
                 "Used by the 'Open in Nuke' buttons, e.g. --nukex or --studio"))
        browse.clicked.connect(self._browse_nuke)
        detect.clicked.connect(self._detect_nuke)
        exe.textChanged.connect(self._validate_exe)
        self._validate_exe()

        # --- Processing
        g = self._group(lay, "Processing")
        g.addRow("Parallel Nuke processes:", self._spin("max_processes", 1, 64,
                 "How many Nuke processes run at the same time. Limited by licences and RAM."))
        g.addRow("Scripts per Nuke process:", self._spin("files_per_process", 1, 1000,
                 "Each Nuke process opens this many scripts one after another, so Nuke's start-up "
                 "time is paid once per batch. Use 1 if your python script leaves state behind."))
        g.addRow("Timeout per script:", self._spin("timeout_per_file", 0, 86400,
                 "Kill Nuke if one script takes longer than this. 0 = no limit.", " s"))
        g.addRow("Start-up / idle timeout:", self._spin("startup_timeout", 0, 86400,
                 "Kill Nuke if it shows no progress for this long (hung on start-up, licence wait...). "
                 "0 = no limit.", " s"))
        if os.name == "nt":
            g.addRow("", self._check("hide_console", "Hide Nuke console windows"))

        # --- Safety
        g = self._group(lay, "Safety")
        g.addRow("", self._check("make_backup", "Make a backup copy before saving",
                                 "Copies script.nk to script.nk<suffix>. An existing backup is never "
                                 "overwritten, so it always holds the original."))
        g.addRow("Backup suffix:", self._line("backup_suffix"))
        g.addRow("", self._check("dry_run", "Dry run - open scripts and run the python script, but never save"))

        # --- Search
        g = self._group(lay, "Search")
        g.addRow("Skip folders named:", self._line("scan_excludes",
                 "Comma separated folder-name patterns that are never searched (renders, plates...). "
                 "Skipping big image folders makes searching much faster."))
        g.addRow("Search threads:", self._spin("scan_threads", 1, 64,
                 "Folders listed in parallel. Higher helps on network storage."))
        g.addRow("Max folder depth:", self._spin("scan_max_depth", 0, 100, "0 = unlimited"))
        g.addRow("Search delay after typing:", self._spin("search_delay_ms", 100, 10000,
                 "Wait this long after the last keystroke before searching.", " ms"))

        # --- Queue & logging
        g = self._group(lay, "Queue && Logging")
        g.addRow("", self._check("restore_queue", "Restore the queue from the last session on start-up"))
        level = QtWidgets.QComboBox()
        level.addItems(config.LOG_LEVELS)
        level.setCurrentText(settings.get("log_level_file"))
        level.currentTextChanged.connect(lambda t: settings.set("log_level_file", t))
        self._widgets["log_level_file"] = level
        g.addRow("Log file level:", level)
        g.addRow("Log file size limit:", self._spin("log_max_kb", 100, 1000000,
                 "The log file rotates when it reaches this size (3 old files kept).", " KB"))

        # --- Files
        g = self._group(lay, "Files")
        g.addRow("Settings file:", self._path_row(settings.path))
        g.addRow("Log file:", self._path_row(log_path()))

        restore = QtWidgets.QPushButton("Restore Defaults")
        restore.clicked.connect(self._restore_defaults)
        bottom = QtWidgets.QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(restore)
        lay.addLayout(bottom)
        lay.addStretch(1)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setWidget(content)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        settings.changed.connect(self._sync_widget)

    # ------------------------------------------------------------ builders
    def _group(self, layout, title):
        box = QtWidgets.QGroupBox(title)
        form = QtWidgets.QFormLayout(box)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        layout.addWidget(box)
        return form

    def _line(self, key, tooltip=None):
        w = QtWidgets.QLineEdit(str(self.settings.get(key)))
        if tooltip:
            w.setToolTip(tooltip)
        w.editingFinished.connect(lambda k=key, w=w: self.settings.set(k, w.text().strip()))
        self._widgets[key] = w
        return w

    def _spin(self, key, lo, hi, tooltip=None, suffix=""):
        w = QtWidgets.QSpinBox()
        w.setRange(lo, hi)
        w.setValue(int(self.settings.get(key)))
        if suffix:
            w.setSuffix(suffix)
        if tooltip:
            w.setToolTip(tooltip)
        w.setMaximumWidth(140)
        w.valueChanged.connect(lambda v, k=key: self.settings.set(k, int(v)))
        self._widgets[key] = w
        return w

    def _check(self, key, text, tooltip=None):
        w = QtWidgets.QCheckBox(text)
        w.setChecked(bool(self.settings.get(key)))
        if tooltip:
            w.setToolTip(tooltip)
        w.toggled.connect(lambda v, k=key: self.settings.set(k, bool(v)))
        self._widgets[key] = w
        return w

    def _path_row(self, path):
        row = QtWidgets.QHBoxLayout()
        label = hint_label(to_slash(path))
        btn = QtWidgets.QPushButton("Open Folder")
        btn.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(
            QtCore.QUrl.fromLocalFile(os.path.dirname(path))))
        row.addWidget(label, 1)
        row.addWidget(btn)
        return row

    # ------------------------------------------------------------ sync
    def _sync_widget(self, key, value):
        """Keep widgets in step when a setting is changed elsewhere."""
        w = self._widgets.get(key)
        if w is None:
            return
        w.blockSignals(True)
        try:
            if isinstance(w, QtWidgets.QLineEdit):
                if w.text() != str(value):
                    w.setText(str(value))
            elif isinstance(w, QtWidgets.QSpinBox):
                w.setValue(int(value))
            elif isinstance(w, QtWidgets.QCheckBox):
                w.setChecked(bool(value))
            elif isinstance(w, QtWidgets.QComboBox):
                w.setCurrentText(str(value))
        finally:
            w.blockSignals(False)
        if key == "nuke_executable":
            self._validate_exe()

    def _validate_exe(self, *_):
        w = self._widgets["nuke_executable"]
        path = w.text().strip()
        ok = bool(path) and os.path.isfile(path)
        set_invalid(w, not ok)
        w.setToolTip("" if ok else "File not found")

    def _browse_nuke(self):
        current = self.settings.get("nuke_executable")
        start = os.path.dirname(current) if current and os.path.isdir(os.path.dirname(current)) else ""
        filt = "Nuke (Nuke*.exe);;All files (*)" if os.name == "nt" else "All files (*)"
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Nuke Executable", start, filt)
        if path:
            self.settings.set("nuke_executable", to_slash(path))

    def _detect_nuke(self):
        found = config.detect_nuke_executables()
        if not found:
            QtWidgets.QMessageBox.information(self, "Detect Nuke", "No Nuke installation found in the "
                                              "default location. Use Browse... instead.")
            return
        if len(found) == 1:
            self.settings.set("nuke_executable", found[0])
            return
        menu = QtWidgets.QMenu(self)
        for path in found:
            menu.addAction(path)
        chosen = qexec(menu, QtGui.QCursor.pos())
        if chosen is not None:
            self.settings.set("nuke_executable", chosen.text())

    def _restore_defaults(self):
        if QtWidgets.QMessageBox.question(
                self, "Restore Defaults", "Reset all settings on this tab to their defaults?\n"
                "(Search fields and the python script are kept.)") != QtWidgets.QMessageBox.Yes:
            return
        self.settings.restore_defaults([k for k in self._widgets])
