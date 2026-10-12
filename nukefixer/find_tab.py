"""'Find Nuke Scripts' tab: background search, version filter, results table."""
import logging
import os
import threading

from .qt import QtCore, QtWidgets, Qt, Signal, qexec
from . import config, scanner, versions
from .models import ResultsModel, make_proxy
from .paths import to_slash
from .widgets import (add_shortcut, open_in_nuke, reveal_in_file_manager, selected_source_rows,
                      set_invalid, setup_table, visible_source_rows)

log = logging.getLogger("nukefixer.find")


class ScanThread(QtCore.QThread):
    """Runs scanner.scan off the GUI thread; progress is read by a GUI timer."""

    def __init__(self, params, parent=None):
        super(ScanThread, self).__init__(parent)
        self.params = params
        self.cancel_event = threading.Event()
        self.dirs = 0
        self.found = 0
        self.result = None
        self.error = None

    def _progress(self, dirs, found):
        self.dirs, self.found = dirs, found

    def run(self):
        try:
            self.result = scanner.scan(cancel=self.cancel_event, progress=self._progress, **self.params)
        except ValueError as exc:
            self.error = str(exc)
        except Exception as exc:   # keep the GUI alive whatever happens
            log.exception("Search failed")
            self.error = "Search failed: %s" % exc


class FindTab(QtWidgets.QWidget):
    addToQueue = Signal(list)          # list of scanner.FoundFile

    def __init__(self, settings, parent=None):
        super(FindTab, self).__init__(parent)
        self.settings = settings
        self.scan_files = []
        self._thread = None
        self._old_threads = []
        self._generation = 0

        s = settings.get
        self.root = QtWidgets.QLineEdit(s("search_start"))
        self.root.setToolTip("Search here and below")
        self.browse = QtWidgets.QPushButton("...")
        self.browse.setFixedWidth(40)
        self.contains = QtWidgets.QLineEdit(s("only_if_contains"))
        self.contains.setToolTip("Only keep results whose full path contains this text, e.g. /work/comp/")
        self.pattern = QtWidgets.QLineEdit(s("search_for"))
        self.pattern.setToolTip("File name pattern (* any text, ? one character), e.g. *_comp_v???.nk")
        self.regex = QtWidgets.QLineEdit(s("version_regex"))
        self.regex.setToolTip("Regular expression searched in the file name. The first (group) is the "
                              "version, compared as a number: _v(\\d+)\\.nk$")
        self.mode_first = QtWidgets.QRadioButton("First")
        self.mode_last = QtWidgets.QRadioButton("Last")
        self.mode_all = QtWidgets.QRadioButton("All")
        {"first": self.mode_first, "all": self.mode_all}.get(s("version_mode"), self.mode_last).setChecked(True)
        self.search_btn = QtWidgets.QPushButton("Search")
        self.search_btn.setToolTip("Search now (Enter in any field). Searching also starts "
                                   "automatically shortly after you stop typing.")
        self.status = QtWidgets.QLabel("Set the search root and press Search.")

        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.addWidget(QtWidgets.QLabel("Search Root Directory:"), 0, 0, Qt.AlignRight)
        row0 = QtWidgets.QHBoxLayout()
        row0.addWidget(self.root)
        row0.addWidget(self.browse)
        grid.addLayout(row0, 0, 1, 1, 3)
        grid.addWidget(QtWidgets.QLabel("Only if contains:"), 1, 0, Qt.AlignRight)
        grid.addWidget(self.contains, 1, 1)
        grid.addWidget(QtWidgets.QLabel("Search for:"), 1, 2, Qt.AlignRight)
        grid.addWidget(self.pattern, 1, 3)
        grid.addWidget(QtWidgets.QLabel("Version Regex:"), 2, 0, Qt.AlignRight)
        grid.addWidget(self.regex, 2, 1)
        grid.addWidget(QtWidgets.QLabel("Apply to Versions:"), 2, 2, Qt.AlignRight)
        modes = QtWidgets.QHBoxLayout()
        for w in (self.mode_first, self.mode_last, self.mode_all):
            modes.addWidget(w)
        modes.addStretch(1)
        modes.addWidget(self.search_btn)
        grid.addLayout(modes, 2, 3)

        self.filter = QtWidgets.QLineEdit()
        self.filter.setPlaceholderText("Filter results...")
        self.filter.setClearButtonEnabled(True)
        status_row = QtWidgets.QHBoxLayout()
        status_row.addWidget(self.status, 1)
        status_row.addWidget(self.filter)

        self.model = ResultsModel(self)
        self.proxy = make_proxy(self.model, self)
        self.view = QtWidgets.QTableView()
        setup_table(self.view, self.proxy)
        self.view.setToolTip("Double-click to show the file in the file manager. "
                             "Space toggles the selected rows.")

        self.all_box = QtWidgets.QCheckBox("All")
        self.all_box.setToolTip("Check / uncheck all visible rows")
        self.count_label = QtWidgets.QLabel("")
        self.nuke_btn = QtWidgets.QPushButton("Open in Nuke")
        self.nuke_btn.setToolTip("Open the selected scripts in interactive Nuke, one session per script "
                                 "(asks first when more than 5)")
        self.nuke_btn.setEnabled(False)
        self.add_btn = QtWidgets.QPushButton("Add to Queue")
        self.add_btn.setToolTip("Add the checked scripts to the Queue tab")
        self.add_btn.setMinimumWidth(180)
        bottom = QtWidgets.QHBoxLayout()
        bottom.addWidget(self.all_box)
        bottom.addWidget(self.count_label, 1)
        bottom.addWidget(self.nuke_btn)
        bottom.addWidget(self.add_btn)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(grid)
        lay.addLayout(status_row)
        lay.addWidget(self.view, 1)
        lay.addLayout(bottom)

        # timers
        self.search_timer = QtCore.QTimer(self, singleShot=True)
        self.search_timer.timeout.connect(self.start_search)
        self.filter_timer = QtCore.QTimer(self, singleShot=True, interval=250)
        self.filter_timer.timeout.connect(self.apply_versions)
        self.progress_timer = QtCore.QTimer(self, interval=200)
        self.progress_timer.timeout.connect(self._show_progress)

        # signals - textEdited (user typing) only, never programmatic changes
        for w in (self.root, self.contains, self.pattern):
            w.textEdited.connect(self._schedule_search)
            w.returnPressed.connect(self.start_search)
        self.regex.textEdited.connect(lambda _t: self.filter_timer.start())
        self.regex.returnPressed.connect(self.apply_versions)
        for w in (self.mode_first, self.mode_last, self.mode_all):
            w.toggled.connect(self._mode_toggled)
        self.browse.clicked.connect(self.browse_root)
        self.search_btn.clicked.connect(self._search_clicked)
        self.filter.textChanged.connect(self.proxy.setFilterFixedString)
        self.filter.textChanged.connect(lambda _t: self._update_counts())
        self.all_box.clicked.connect(self._all_clicked)
        self.add_btn.clicked.connect(self._add_clicked)
        self.model.countsChanged.connect(self._update_counts)
        self.view.doubleClicked.connect(self._reveal_index)
        self.nuke_btn.clicked.connect(self.open_selected_in_nuke)
        self.view.selectionModel().selectionChanged.connect(
            lambda *_: self.nuke_btn.setEnabled(bool(selected_source_rows(self.view, self.proxy))))
        self.view.customContextMenuRequested.connect(self._context_menu)
        add_shortcut(self.view, "Space", self._toggle_selected)
        self._update_counts()

    # ------------------------------------------------------------ settings
    def version_mode(self):
        if self.mode_first.isChecked():
            return "first"
        if self.mode_all.isChecked():
            return "all"
        return "last"

    def store_settings(self):
        st = self.settings
        st.set("search_start", to_slash(self.root.text().strip()))
        st.set("only_if_contains", self.contains.text())
        st.set("search_for", self.pattern.text())
        st.set("version_regex", self.regex.text())
        st.set("version_mode", self.version_mode())

    # ------------------------------------------------------------- search
    def _schedule_search(self, _text=None):
        self.store_settings()
        self.search_timer.start(max(100, int(self.settings.get("search_delay_ms"))))

    def _search_clicked(self):
        if self._thread is not None:
            self.cancel_search()
            self.status.setText("Search cancelled.")
        else:
            self.start_search()

    def browse_root(self):
        start = self.root.text().strip()
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Search Root Folder", start if os.path.isdir(start) else "")
        if not folder:            # cancelled - keep the current root
            return
        self.root.setText(to_slash(os.path.normpath(folder)))
        self.start_search()

    def cancel_search(self):
        self.search_timer.stop()
        if self._thread is not None:
            self._thread.cancel_event.set()
            self._old_threads.append(self._thread)   # keep alive until it ends
            self._thread = None
        self.progress_timer.stop()
        self.search_btn.setText("Search")

    def start_search(self):
        self.search_timer.stop()
        self.store_settings()
        self.cancel_search()
        root = self.root.text().strip()
        error = None
        if not root:
            error = "Choose a search root folder."
        elif not os.path.isdir(root):
            error = "Search root does not exist: %s" % root
        set_invalid(self.root, bool(error))
        if not error and not self.pattern.text().strip():
            error = "'Search for' pattern is empty."
        set_invalid(self.pattern, not self.pattern.text().strip())
        if error:
            self._set_status(error, True)
            return

        self._generation += 1
        params = dict(
            root=root,
            pattern=self.pattern.text().strip(),
            contains=self.contains.text().strip(),
            excludes=config.parse_list(self.settings.get("scan_excludes")),
            threads=self.settings.get("scan_threads"),
            max_depth=self.settings.get("scan_max_depth"),
        )
        log.info("Searching %s for %s (contains '%s')", root, params["pattern"], params["contains"])
        thread = ScanThread(params, self)
        gen = self._generation
        thread.finished.connect(lambda t=thread, g=gen: self._scan_finished(t, g))
        self._thread = thread
        self.search_btn.setText("Cancel")
        self._set_status("Searching...", False)
        self.progress_timer.start()
        thread.start()

    def _show_progress(self):
        t = self._thread
        if t is not None:
            self._set_status("Searching... %d folders, %d matching files" % (t.dirs, t.found), False)

    def _scan_finished(self, thread, generation):
        if thread in self._old_threads:
            self._old_threads.remove(thread)
        thread.deleteLater()
        if generation != self._generation or thread is not self._thread:
            return                                  # stale or cancelled search
        self._thread = None
        self.progress_timer.stop()
        self.search_btn.setText("Search")
        if thread.error:
            self._set_status(thread.error, True)
            return
        res = thread.result
        self.scan_files = res.files
        self._last_scan_text = "%d files in %d folders searched in %.1f s%s" % (
            len(res.files), res.dirs_scanned, res.elapsed,
            (", %d unreadable folders" % res.errors) if res.errors else "")
        log.info("Search finished: %s", self._last_scan_text)
        self.apply_versions(keep_checks=False)

    def apply_versions(self, keep_checks=True):
        self.store_settings()
        rx, err = versions.compile_version_regex(self.regex.text())
        set_invalid(self.regex, bool(err))
        if err:
            self._set_status(err, True)
            return
        unchecked = set()
        if keep_checks:
            unchecked = {c.path for c in self.model.candidates()} - {c.path for c in self.model.candidates(True)}
        candidates, unmatched = versions.select_versions(self.scan_files, rx, self.version_mode())
        self.model.set_candidates(candidates)
        if unchecked:
            rows = [r for r, c in enumerate(candidates) if c.path in unchecked]
            self.model.set_checked(rows, False)
        self.view.resizeColumnsToContents()
        self.view.setColumnWidth(0, 28)
        if not self.scan_files and not getattr(self, "_last_scan_text", None):
            return
        text = "Found %s. Showing %d (%s version%s)" % (
            getattr(self, "_last_scan_text", "0 files"), len(candidates), self.version_mode(),
            "s" if self.version_mode() == "all" else "")
        if unmatched:
            text += "; %d file(s) don't match the version regex" % unmatched
        self._set_status(text + ".", False)

    def _set_status(self, text, error):
        self.status.setText(text)
        self.status.setObjectName("statusError" if error else "")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def _mode_toggled(self, on):
        if on:
            self.apply_versions()

    # ------------------------------------------------------------- table
    def _update_counts(self):
        total = self.model.rowCount()
        checked = self.model.checked_count()
        shown = self.proxy.rowCount()
        text = "%d of %d checked" % (checked, total)
        if shown != total:
            text += " (%d shown)" % shown
        self.count_label.setText(text)
        self.all_box.setChecked(total > 0 and checked == total)
        self.add_btn.setEnabled(checked > 0)
        self.add_btn.setText("Add %d to Queue" % checked if checked else "Add to Queue")

    def _all_clicked(self, checked):
        self.model.set_checked(visible_source_rows(self.proxy), checked)

    def _toggle_selected(self):
        rows = selected_source_rows(self.view, self.proxy)
        if rows:
            state = not all(self.model.is_row_checked(r) for r in rows)
            self.model.set_checked(rows, state)

    def _reveal_index(self, index):
        if index.isValid() and index.column() != 0:
            reveal_in_file_manager(self.model.candidate(self.proxy.mapToSource(index).row()).path)

    def _context_menu(self, pos):
        rows = selected_source_rows(self.view, self.proxy)
        menu = QtWidgets.QMenu(self)
        a_show = menu.addAction("Show in File Manager")
        a_nuke = menu.addAction("Open in Nuke")
        menu.addSeparator()
        a_check = menu.addAction("Check Selected")
        a_uncheck = menu.addAction("Uncheck Selected")
        a_add = menu.addAction("Add Selected to Queue")
        a_copy = menu.addAction("Copy Paths")
        for a in (a_show, a_nuke, a_check, a_uncheck, a_add, a_copy):
            a.setEnabled(bool(rows))
        chosen = qexec(menu, self.view.viewport().mapToGlobal(pos))
        if chosen is None:
            return
        if chosen == a_show:
            reveal_in_file_manager(self.model.candidate(rows[0]).path)
        elif chosen == a_nuke:
            self.open_selected_in_nuke()
        elif chosen == a_check:
            self.model.set_checked(rows, True)
        elif chosen == a_uncheck:
            self.model.set_checked(rows, False)
        elif chosen == a_add:
            self.addToQueue.emit([self.model.candidate(r).file for r in rows])
        elif chosen == a_copy:
            QtWidgets.QApplication.clipboard().setText(
                "\n".join(self.model.candidate(r).path for r in rows))

    def open_selected_in_nuke(self):
        rows = selected_source_rows(self.view, self.proxy)
        open_in_nuke(self, self.settings, [self.model.candidate(r).path for r in rows])

    def _add_clicked(self):
        files = [c.file for c in self.model.candidates(checked_only=True)]
        if files:
            self.addToQueue.emit(files)

    def set_queued_keys(self, keys):
        self.model.set_queued_keys(keys)

    def shutdown(self):
        self.cancel_search()
        for t in list(self._old_threads):
            t.wait(5000)
