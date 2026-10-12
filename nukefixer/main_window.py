"""Main window: tabs, bottom Execute bar, run control with progress and ETA."""
import base64
import logging
import os
import time

from .qt import QtCore, QtGui, QtWidgets, QShortcut, qexec
from . import APP_NAME, __version__
from .eta import EtaTracker
from .find_tab import FindTab
from .log_tab import LogTab, NUKE_LOGGER, set_file_level
from .paths import images_dir, log_path, runner_script, to_slash
from .queue_io import DONE, FAILED, PENDING, RUNNING, human_time
from .queue_tab import QueueTab
from .runner import NukePool, build_command
from .script_tab import ScriptTab
from .settings_tab import SettingsTab

log = logging.getLogger("nukefixer")
nuke_log = logging.getLogger(NUKE_LOGGER)

ETA_RECALC_SECONDS = 5.0
AUTOSAVE_SECONDS = 15.0


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, settings, parent=None):
        super(MainWindow, self).__init__(parent)
        self.settings = settings
        self.pool = None
        self.tracker = EtaTracker()
        self._eta_deadline = None
        self._eta_calc_time = 0.0
        self._last_autosave = 0.0
        self._run_paths = set()
        self._polling = False

        self.setWindowTitle("%s %s – Beware! Dangerous Toy" % (APP_NAME, __version__))
        icon = os.path.join(images_dir(), "folder.png")
        if os.path.isfile(icon):
            self.setWindowIcon(QtGui.QIcon(icon))

        # --- tabs
        self.tabs = QtWidgets.QTabWidget()
        self.find_tab = FindTab(settings)
        self.script_tab = ScriptTab(settings)
        self.queue_tab = QueueTab(settings)
        self.log_tab = LogTab(log_path(), settings.get("log_level_view"), settings.get("log_show_nuke_output"))
        self.settings_tab = SettingsTab(settings)
        self.tabs.addTab(self.find_tab, "Find Nuke Scripts")
        self.tabs.addTab(self.script_tab, "Python Script")
        self.tabs.addTab(self.queue_tab, "Queue")
        self.tabs.addTab(self.log_tab, "Log")
        self.tabs.addTab(self.settings_tab, "Settings")

        # --- bottom bar
        self.progress = QtWidgets.QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setVisible(False)
        self.run_status = QtWidgets.QLabel("")
        self.run_status.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.dry_run = QtWidgets.QCheckBox("Dry run (don't save)")
        self.dry_run.setToolTip("Open every script and run the python script, but never save. "
                                "Good for testing a script on the whole queue.")
        self.dry_run.setChecked(settings.get("dry_run"))
        self.execute = QtWidgets.QPushButton("Execute")
        self.execute.setObjectName("execute")
        self.execute.setMinimumHeight(50)
        self.execute.setToolTip("Run the python script on every checked, pending script in the Queue. "
                                "While running: stop (Ctrl+.)")

        exec_row = QtWidgets.QHBoxLayout()
        exec_row.addWidget(self.dry_run)
        exec_row.addWidget(self.execute, 1)

        central = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(central)
        lay.addWidget(self.tabs, 1)
        lay.addWidget(self.progress)
        lay.addWidget(self.run_status)
        lay.addLayout(exec_row)
        self.setCentralWidget(central)

        # --- timers
        self.poll_timer = QtCore.QTimer(self, interval=100)
        self.poll_timer.timeout.connect(self._poll)
        self.ui_timer = QtCore.QTimer(self, interval=1000)
        self.ui_timer.timeout.connect(self._update_run_status)

        # --- signals
        self.find_tab.addToQueue.connect(self._add_to_queue)
        self.queue_tab.countsChanged.connect(self._update_execute)
        self.queue_tab.countsChanged.connect(self._update_queued_marks)
        self.execute.clicked.connect(self._execute_clicked)
        self.dry_run.toggled.connect(lambda on: settings.set("dry_run", bool(on)))
        self.log_tab.levelChanged.connect(lambda t: settings.set("log_level_view", t))
        self.log_tab.nukeOutputChanged.connect(lambda on: settings.set("log_show_nuke_output", bool(on)))
        settings.changed.connect(self._setting_changed)
        self.stop_shortcut = QShortcut(QtGui.QKeySequence("Ctrl+."), self)
        self.stop_shortcut.activated.connect(self._request_stop)

        # --- restore state
        geo = settings.get("window_geometry")
        if geo:
            try:
                self.restoreGeometry(QtCore.QByteArray(base64.b64decode(geo)))
            except (ValueError, TypeError):
                self.resize(1400, 850)
        else:
            self.resize(1400, 850)
        if settings.get("restore_queue"):
            self.queue_tab.restore_autosave()
        self.tabs.setCurrentIndex(max(0, min(self.tabs.count() - 1, settings.get("current_tab"))))
        self._update_execute()
        self._update_queued_marks()
        log.info("%s %s started. Settings: %s", APP_NAME, __version__, to_slash(settings.path))

    # ================================================================ queue
    def _add_to_queue(self, files):
        added, skipped = self.queue_tab.add_files(files)
        text = "Added %d script(s) to the queue" % added
        if skipped:
            text += ", %d already there" % skipped
        self.statusBar().showMessage(text + ".", 6000)
        self.queue_tab.autosave()

    def _update_queued_marks(self):
        self.find_tab.set_queued_keys(self.queue_tab.model.keys())

    def _update_execute(self):
        count = self.queue_tab.model.counts()
        self.tabs.setTabText(2, "Queue (%d)" % count["total"] if count["total"] else "Queue")
        if self.pool is not None:
            return
        n = count["runnable"]
        if n == 0:
            self.execute.setText("Nothing to execute – add scripts to the Queue" if not count["total"]
                                 else "Nothing to execute – no checked, pending scripts in the Queue")
            self.execute.setEnabled(False)
            return
        self.execute.setEnabled(True)
        noun = "Nuke script" if n == 1 else "Nuke scripts"
        if self.settings.get("dry_run"):
            self.execute.setText("Execute DRY RUN on %d %s (nothing will be saved)" % (n, noun))
        else:
            self.execute.setText("Execute – modify %d %s" % (n, noun))

    def _setting_changed(self, key, value):
        if key == "dry_run":
            if self.dry_run.isChecked() != bool(value):
                self.dry_run.blockSignals(True)
                self.dry_run.setChecked(bool(value))
                self.dry_run.blockSignals(False)
            self._update_execute()
        elif key == "log_level_file":
            set_file_level(value)

    # ================================================================ run
    def _execute_clicked(self):
        if self.pool is not None:
            self._request_stop()
            return
        self._start_run()

    def _preflight(self):
        errors = []
        exe = self.settings.get("nuke_executable").strip()
        if not exe or not os.path.isfile(exe):
            errors.append("Nuke executable not found:\n  %s\nSet it on the Settings tab." % (exe or "(empty)"))
        err = self.script_tab.check_syntax()
        if err:
            errors.append("Python script: " + err)
        if not os.path.isfile(runner_script()):
            errors.append("Runner script missing: %s" % runner_script())
        return errors

    def _start_run(self):
        items = self.queue_tab.model.runnable()
        if not items:
            return
        if self.queue_tab.busy:
            QtWidgets.QMessageBox.information(self, "Execute", "Wait until the roll-back has finished.")
            return
        errors = self._preflight()
        if errors:
            QtWidgets.QMessageBox.critical(self, "Cannot Execute", "\n\n".join(errors))
            return
        s = self.settings.get
        dry = bool(s("dry_run"))
        procs = min(int(s("max_processes")), len(items))
        details = ["%d Nuke script(s) will be %s." % (len(items), "opened (DRY RUN, nothing saved)" if dry
                                                     else "opened, modified and SAVED"),
                   "Up to %d Nuke process(es) in parallel, %d script(s) per process." % (procs, s("files_per_process")),
                   "Backups: %s" % (("on (%s)" % s("backup_suffix")) if s("make_backup") and not dry else "off"),
                   "Nuke: %s" % s("nuke_executable")]
        box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning if not dry else QtWidgets.QMessageBox.Question,
                                    "Do or don't, there is no try!", "\n".join(details), parent=self)
        box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
        box.setDefaultButton(QtWidgets.QMessageBox.Cancel)
        qexec(box)
        if box.clickedButton() != box.button(QtWidgets.QMessageBox.Yes):
            return

        self.settings.save()
        command = build_command(s("nuke_executable").strip(), s("interactive_license"), s("nuke_extra_args"))
        self.pool = NukePool(
            command, runner_script(), self.script_tab.text(),
            script_dir=self.script_tab.script_dir(),
            max_processes=s("max_processes"), files_per_process=s("files_per_process"),
            timeout_per_file=s("timeout_per_file"), startup_timeout=s("startup_timeout"),
            make_backup=s("make_backup"), backup_suffix=s("backup_suffix"),
            dry_run=dry, hide_console=s("hide_console"))
        paths = [it.path for it in items]
        self._run_paths = set(paths)
        try:
            self.pool.start(paths)
        except Exception as exc:
            log.exception("Could not start the run")
            QtWidgets.QMessageBox.critical(self, "Cannot Execute", str(exc))
            self.pool = None
            return

        now = time.time()
        self.tracker.reset(len(paths), now)
        self._eta_deadline, self._eta_calc_time = None, 0.0
        self._last_autosave = now
        self.queue_tab.set_running(True)
        self.dry_run.setEnabled(False)
        self.progress.setRange(0, len(paths))
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.execute.setProperty("running", "true")
        self.execute.style().unpolish(self.execute)
        self.execute.style().polish(self.execute)
        self.poll_timer.start()
        self.ui_timer.start()
        self._poll()
        self._update_run_status()

    def _request_stop(self):
        if self.pool is None or not self.pool.is_active:
            return
        box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "Stop",
                                    "Stop processing?\n\n%d script(s) are being processed right now."
                                    % self.pool.running_count, parent=self)
        b_graceful = box.addButton("Finish Current, Then Stop", QtWidgets.QMessageBox.AcceptRole)
        b_kill = box.addButton("Kill Nuke Now", QtWidgets.QMessageBox.DestructiveRole)
        box.addButton("Keep Running", QtWidgets.QMessageBox.RejectRole)
        qexec(box)
        if self.pool is None:
            return
        if box.clickedButton() == b_graceful:
            log.warning("Stop requested - finishing the scripts in progress")
            self.pool.stop(kill=False)
        elif box.clickedButton() == b_kill:
            log.warning("Stop requested - killing Nuke processes")
            self.pool.stop(kill=True)
        self._update_run_status()

    def _poll(self):
        if self.pool is None or self._polling:
            return
        self._polling = True
        try:
            self._poll_once()
        finally:
            self._polling = False

    def _poll_once(self):
        try:
            events = self.pool.poll()
        except Exception:
            log.exception("Runner error - killing all Nuke processes")
            self.pool.stop(kill=True)
            return
        model = self.queue_tab.model
        progress_changed = False
        for ev in events:
            kind = ev[0]
            if kind == "start":
                it = model.item_for_path(ev[1])
                if it is not None:
                    it.status, it.message, it.duration = RUNNING, "", None
                    model.item_changed(ev[1])
                log.debug("Processing %s", ev[1])
            elif kind == "result":
                _, path, ok, saved, message, duration, backup = ev
                it = model.item_for_path(path)
                if it is not None:
                    it.status = DONE if ok else FAILED
                    it.saved = saved if ok else False
                    it.message = (message or "").strip()
                    it.duration = duration
                    if backup:
                        it.backup = backup
                    it.finished_at = time.time()
                    it.refresh_stat()
                    model.item_changed(path)
                self.tracker.add_done(ok)
                progress_changed = True
                if ok:
                    log.info("OK      %s  (%s, %s)", path, message, human_time(duration))
                else:
                    log.error("FAILED  %s\n%s", path, (message or "").strip())
            elif kind == "message":
                log.info("script: %s: %s", os.path.basename(ev[1] or ""), ev[2])
            elif kind == "output":
                nuke_log.debug("%s%s", ("[%s] " % os.path.basename(ev[1])) if ev[1] else "", ev[2])
            elif kind == "log":
                log.log(ev[1], ev[2])
            elif kind == "fatal":
                log.error(ev[1])
                QtCore.QTimer.singleShot(0, lambda m=ev[1]: QtWidgets.QMessageBox.critical(self, "Run Aborted", m))
            elif kind == "finished":
                self._run_finished(ev[1])
                return
        if progress_changed:
            self.progress.setValue(self.tracker.done)
            self._recalc_eta(force=True)
            self._update_run_status()
        if time.time() - self._last_autosave > AUTOSAVE_SECONDS:
            self._last_autosave = time.time()
            self.queue_tab.autosave()

    def _recalc_eta(self, force=False):
        now = time.time()
        if not force and now - self._eta_calc_time < ETA_RECALC_SECONDS:
            return
        if force and now - self._eta_calc_time < 1.0:
            return
        self._eta_calc_time = now
        eta = self.tracker.eta(now)
        self._eta_deadline = None if eta is None else now + eta

    def _update_run_status(self):
        if self.pool is None:
            return
        self._recalc_eta()
        now = time.time()
        t = self.tracker
        parts = ["%d / %d done" % (t.done, t.total)]
        if t.failed:
            parts.append("%d failed" % t.failed)
        parts.append("%d Nuke running" % self.pool.running_count)
        parts.append("elapsed %s" % human_time(t.elapsed(now)))
        rate = t.rate(now)
        if rate:
            parts.append("%.1f s/script" % (1.0 / rate))
        if self.pool.state == "stopping":
            parts.append("STOPPING – waiting for running scripts")
        elif self._eta_deadline is None:
            parts.append("estimating time left...")
        else:
            left = max(0.0, self._eta_deadline - now)
            parts.append("ETA %s (around %s)" % (human_time(left),
                                                 time.strftime("%H:%M", time.localtime(self._eta_deadline))))
        text = "  ·  ".join(parts)
        self.run_status.setText(text)
        self.progress.setFormat("%p%  (%v / %m)")
        verb = "Stopping" if self.pool.state == "stopping" else "Stop"
        self.execute.setText("%s  –  %d / %d processed (Ctrl+.)" % (verb, t.done, t.total))
        self.setWindowTitle("[%d/%d] %s" % (t.done, t.total, APP_NAME))

    def _run_finished(self, summary):
        self.poll_timer.stop()
        self.ui_timer.stop()
        pool, self.pool = self.pool, None
        model = self.queue_tab.model
        for path in self._run_paths:            # anything left 'running' was not finished
            it = model.item_for_path(path)
            if it is not None and it.status == RUNNING:
                it.status = PENDING
                model.item_changed(path)
        self._run_paths = set()
        self.queue_tab.set_running(False)
        self.queue_tab.autosave()
        self.dry_run.setEnabled(True)
        self.progress.setVisible(False)
        self.execute.setProperty("running", "false")
        self.execute.style().unpolish(self.execute)
        self.execute.style().polish(self.execute)
        self.setWindowTitle("%s %s – Beware! Dangerous Toy" % (APP_NAME, __version__))

        text = "Finished in %s: %d OK, %d failed" % (human_time(summary["elapsed"]), summary["ok"], summary["failed"])
        if summary["not_run"]:
            text += ", %d not run (stopped)" % summary["not_run"]
        if pool is not None and pool.dry_run:
            text += "  [dry run – nothing saved]"
        self.run_status.setText(text + ".")
        (log.warning if summary["failed"] or summary["fatal"] else log.info)(text)
        self._update_execute()
        QtWidgets.QApplication.alert(self)
        if summary["failed"]:
            self.statusBar().showMessage("Some scripts failed – see the Queue tab (hover the message) "
                                         "and the Log tab.", 15000)

    # ================================================================ close
    def closeEvent(self, event):
        if self.pool is not None and self.pool.is_active:
            answer = QtWidgets.QMessageBox.question(
                self, "Quit", "Nuke scripts are still being processed.\nKill the Nuke processes and quit?")
            if answer != QtWidgets.QMessageBox.Yes:
                event.ignore()
                return
            self.pool.stop(kill=True)
            deadline = time.time() + 5
            while self.pool is not None and self.pool.is_active and time.time() < deadline:
                self._poll()
                QtCore.QThread.msleep(50)
        self.find_tab.store_settings()
        self.find_tab.shutdown()
        self.queue_tab.shutdown()
        self.queue_tab.autosave()
        self.settings.set("current_tab", self.tabs.currentIndex())
        self.settings.set("window_geometry", base64.b64encode(bytes(self.saveGeometry().data())).decode("ascii"))
        self.settings.save()
        self.log_tab.shutdown()
        event.accept()
