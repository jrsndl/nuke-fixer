"""'Queue' tab: the scripts that Execute will process, with status and stats."""
import logging
import os

from .qt import QtCore, QtWidgets, Signal, qexec
from . import queue_io
from .queue_io import (DONE, FAILED, PENDING, RB_CHANGED, RB_NO_BACKUP, RB_NOT_DONE, RB_OK,
                       human_size, plan_rollback, rollback_file)
from .models import QueueModel, make_proxy
from .paths import autosave_queue_path, to_slash
from .widgets import add_shortcut, open_in_nuke, reveal_in_file_manager, selected_source_rows, setup_table

log = logging.getLogger("nukefixer.queue")

QUEUE_FILTER = "NukeFixer queue (*.json);;Text list of .nk paths (*.txt);;All files (*)"


class StatThread(QtCore.QThread):
    """Re-reads size / modification date of queue files off the GUI thread."""

    def __init__(self, paths, parent=None):
        super(StatThread, self).__init__(parent)
        self.paths = paths
        self.stats = {}

    def run(self):
        for p in self.paths:
            try:
                st = os.stat(p)
                self.stats[p] = (st.st_size, st.st_mtime)
            except OSError:
                self.stats[p] = None


class RollbackThread(QtCore.QThread):
    """Restores backups off the GUI thread (renames on network shares can be slow)."""

    def __init__(self, pairs, parent=None):
        super(RollbackThread, self).__init__(parent)
        self.pairs = pairs            # [(path, backup)]
        self.results = []             # [(path, ok, message)]

    def run(self):
        for path, backup in self.pairs:
            ok, message = rollback_file(path, backup)
            self.results.append((path, ok, message))


class QueueTab(QtWidgets.QWidget):
    countsChanged = Signal()

    def __init__(self, settings, parent=None):
        super(QueueTab, self).__init__(parent)
        self.settings = settings
        self.model = QueueModel(self)
        self.proxy = make_proxy(self.model, self)
        self._stat_thread = None
        self._rollback_thread = None
        self._running = False

        self.load_btn = QtWidgets.QPushButton("Load...")
        self.save_btn = QtWidgets.QPushButton("Save...")
        self.export_btn = QtWidgets.QPushButton("Export Report...")
        self.export_btn.setToolTip("Save the queue with status and messages as CSV")
        self.remove_btn = QtWidgets.QPushButton("Remove Selected")
        self.remove_done_btn = QtWidgets.QPushButton("Remove Done")
        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.reset_btn = QtWidgets.QPushButton("Reset Selected")
        self.reset_btn.setToolTip("Set the selected scripts back to Pending so Execute runs them again")
        self.retry_btn = QtWidgets.QPushButton("Retry Failed")
        self.rollback_btn = QtWidgets.QPushButton("Roll Back...")
        self.rollback_btn.setToolTip(
            "Undo NukeFixer's changes: delete the modified script and rename its backup copy back "
            "to the original name.\nWorks on the selected scripts, or on all Done scripts if none "
            "are selected.")
        self.stats_btn = QtWidgets.QPushButton("Refresh Stats")
        self.stats_btn.setToolTip("Re-read file sizes and modification dates")

        bar = QtWidgets.QHBoxLayout()
        for w in (self.load_btn, self.save_btn, self.export_btn):
            bar.addWidget(w)
        bar.addSpacing(16)
        for w in (self.remove_btn, self.remove_done_btn, self.clear_btn):
            bar.addWidget(w)
        bar.addSpacing(16)
        for w in (self.reset_btn, self.retry_btn, self.rollback_btn, self.stats_btn):
            bar.addWidget(w)
        bar.addStretch(1)

        self.check_btn = QtWidgets.QPushButton("Check Selected")
        self.check_btn.setToolTip("Tick the selected rows so Execute processes them (Space toggles)")
        self.uncheck_btn = QtWidgets.QPushButton("Uncheck Selected")
        self.uncheck_btn.setToolTip("Untick the selected rows so Execute skips them")
        self.nuke_btn = QtWidgets.QPushButton("Open in Nuke")
        self.nuke_btn.setToolTip("Open the selected scripts in interactive Nuke, one session per script "
                                 "(asks first when more than 5)")
        self.summary = QtWidgets.QLabel("")
        self.filter = QtWidgets.QLineEdit()
        self.filter.setPlaceholderText("Filter (path, status, message)...")
        self.filter.setClearButtonEnabled(True)
        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(self.check_btn)
        row2.addWidget(self.uncheck_btn)
        row2.addWidget(self.nuke_btn)
        row2.addSpacing(16)
        row2.addWidget(self.summary, 1)
        row2.addWidget(self.filter)

        self.view = QtWidgets.QTableView()
        setup_table(self.view, self.proxy)
        self.view.setToolTip("Double-click to show the file. Hover the message for the full error. "
                             "Space toggles the selected rows. Delete removes them.")

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(bar)
        lay.addLayout(row2)
        lay.addWidget(self.view, 1)

        self.load_btn.clicked.connect(self.load_dialog)
        self.save_btn.clicked.connect(self.save_dialog)
        self.export_btn.clicked.connect(self.export_dialog)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.remove_done_btn.clicked.connect(lambda: self.model.remove_where(lambda it: it.status == DONE))
        self.clear_btn.clicked.connect(self.clear)
        self.reset_btn.clicked.connect(self.reset_selected)
        self.retry_btn.clicked.connect(self.retry_failed)
        self.stats_btn.clicked.connect(self.refresh_stats)
        self.rollback_btn.clicked.connect(self.rollback_dialog)
        self.check_btn.clicked.connect(lambda: self.check_selected(True))
        self.uncheck_btn.clicked.connect(lambda: self.check_selected(False))
        self.nuke_btn.clicked.connect(self.open_selected_in_nuke)
        self.view.selectionModel().selectionChanged.connect(self._update_check_buttons)
        self.filter.textChanged.connect(self.proxy.setFilterFixedString)
        self.model.countsChanged.connect(self._on_counts)
        self.view.doubleClicked.connect(self._reveal_index)
        self.view.customContextMenuRequested.connect(self._context_menu)
        add_shortcut(self.view, "Space", self._toggle_selected)
        add_shortcut(self.view, "Delete", self.remove_selected)
        self._on_counts()
        self._update_check_buttons()

    # ------------------------------------------------------------ state
    def set_running(self, running):
        self._running = running
        self.model.set_locked(running)
        for w in (self.load_btn, self.remove_btn, self.remove_done_btn, self.clear_btn,
                  self.reset_btn, self.retry_btn, self.stats_btn, self.rollback_btn):
            w.setEnabled(not running and self._rollback_thread is None)
        self._update_check_buttons()

    def _on_counts(self):
        c = self.model.counts()
        total_size = sum(it.size or 0 for it in self.model.items)
        parts = ["%d scripts" % c["total"], "%d pending" % c[PENDING]]
        if c["running"]:
            parts.append("%d running" % c["running"])
        parts += ["%d done" % c[DONE], "%d failed" % c[FAILED]]
        if c["disabled"]:
            parts.append("%d unchecked" % c["disabled"])
        parts.append(human_size(total_size))
        self.summary.setText("  \u00b7  ".join(parts))
        self.countsChanged.emit()

    # ------------------------------------------------------------ adding
    def add_files(self, found_files):
        added, skipped = self.model.add_files(found_files)
        msg = "Added %d script(s) to the queue" % added
        if skipped:
            msg += " (%d already queued)" % skipped
        log.info(msg)
        if added:
            self.view.resizeColumnToContents(1)
            self.view.resizeColumnToContents(2)
        return added, skipped

    # ------------------------------------------------------------ editing
    def _selected(self):
        return selected_source_rows(self.view, self.proxy)

    def remove_selected(self):
        if not self._running:
            self.model.remove_rows(self._selected())

    def clear(self):
        if not self.model.items:
            return
        if QtWidgets.QMessageBox.question(self, "Clear Queue", "Remove all %d scripts from the queue?"
                                          % len(self.model.items)) == QtWidgets.QMessageBox.Yes:
            self.model.set_items([])

    def reset_selected(self):
        self.model.set_status(self._selected(), PENDING)

    def retry_failed(self):
        rows = [r for r, it in enumerate(self.model.items) if it.status == FAILED]
        self.model.set_status(rows, PENDING)
        log.info("%d failed script(s) set back to pending", len(rows))

    def check_selected(self, checked):
        if self._running:
            return
        rows = self._selected()
        if rows:
            self.model.set_enabled(rows, checked)

    def _update_check_buttons(self, *_):
        selected = bool(self._selected())
        self.check_btn.setEnabled(selected and not self._running)
        self.uncheck_btn.setEnabled(selected and not self._running)
        self.nuke_btn.setEnabled(selected)

    def open_selected_in_nuke(self):
        open_in_nuke(self, self.settings, [self.model.item(r).path for r in self._selected()])

    def _toggle_selected(self):
        if self._running:
            return
        rows = self._selected()
        if rows:
            state = not all(self.model.item(r).enabled for r in rows)
            self.model.set_enabled(rows, state)

    def _reveal_index(self, index):
        if index.isValid() and index.column() != 0:
            reveal_in_file_manager(self.model.item(self.proxy.mapToSource(index).row()).path)

    def _context_menu(self, pos):
        rows = self._selected()
        menu = QtWidgets.QMenu(self)
        a_show = menu.addAction("Show in File Manager")
        a_nuke = menu.addAction("Open in Nuke")
        a_copy = menu.addAction("Copy Paths")
        a_msg = menu.addAction("Copy Message")
        menu.addSeparator()
        a_check = menu.addAction("Check Selected")
        a_uncheck = menu.addAction("Uncheck Selected")
        a_reset = menu.addAction("Reset to Pending")
        a_rollback = menu.addAction("Roll Back to Backup...")
        a_remove = menu.addAction("Remove")
        for a in (a_show, a_nuke, a_copy, a_msg):
            a.setEnabled(bool(rows))
        for a in (a_check, a_uncheck, a_reset, a_rollback, a_remove):
            a.setEnabled(bool(rows) and not self._running and self._rollback_thread is None)
        chosen = qexec(menu, self.view.viewport().mapToGlobal(pos))
        if chosen is None:
            return
        items = [self.model.item(r) for r in rows]
        if chosen == a_show:
            reveal_in_file_manager(items[0].path)
        elif chosen == a_nuke:
            open_in_nuke(self, self.settings, [it.path for it in items])
        elif chosen == a_copy:
            QtWidgets.QApplication.clipboard().setText("\n".join(it.path for it in items))
        elif chosen == a_msg:
            QtWidgets.QApplication.clipboard().setText(
                "\n\n".join("%s\n%s" % (it.path, it.message) for it in items if it.message))
        elif chosen == a_check:
            self.model.set_enabled(rows, True)
        elif chosen == a_uncheck:
            self.model.set_enabled(rows, False)
        elif chosen == a_reset:
            self.model.set_status(rows, PENDING)
        elif chosen == a_rollback:
            self.rollback_dialog()
        elif chosen == a_remove:
            self.model.remove_rows(rows)

    # ------------------------------------------------------------ roll-back
    def rollback_dialog(self):
        if self._running or self._rollback_thread is not None:
            return
        rows = self._selected()
        if rows:
            items, scope = [self.model.item(r) for r in rows], "selected"
        else:
            items, scope = [it for it in self.model.items if it.status == DONE], "Done"
        plan = plan_rollback(items, self.settings.get("backup_suffix"))
        ok = [(it, bak) for it, bak, v in plan if v == RB_OK]
        changed = [(it, bak) for it, bak, v in plan if v == RB_CHANGED]
        no_backup = sum(1 for _, _, v in plan if v == RB_NO_BACKUP)
        not_done = sum(1 for _, _, v in plan if v == RB_NOT_DONE)

        notes = []
        if no_backup:
            notes.append("%d script(s) have no backup copy and are skipped." % no_backup)
        if not_done:
            notes.append("%d script(s) were not processed (not Done) and are skipped." % not_done)
        if not ok and not changed:
            QtWidgets.QMessageBox.information(
                self, "Roll Back", "Nothing to roll back in the %s scripts.\n\n%s"
                % (scope, "\n".join(notes) or "Process some scripts first."))
            return

        text = ("Roll back %d %s script(s)?\n\nThe modified script is DELETED and its backup copy "
                "is renamed back to the original name. This cannot be undone."
                % (len(ok) + len(changed), scope))
        if changed:
            listing = "\n".join("  " + it.name for it, _ in changed[:10])
            if len(changed) > 10:
                listing += "\n  ... and %d more" % (len(changed) - 10)
            text += ("\n\nWARNING: %d script(s) were modified AFTER NukeFixer saved them. "
                     "Rolling them back throws those changes away:\n%s" % (len(changed), listing))
        if notes:
            text += "\n\n" + "\n".join(notes)

        box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Roll Back", text, parent=self)
        b_all = box.addButton("Roll Back %d" % (len(ok) + len(changed)), QtWidgets.QMessageBox.DestructiveRole)
        b_safe = None
        if changed and ok:
            b_safe = box.addButton("Skip Modified, Roll Back %d" % len(ok), QtWidgets.QMessageBox.AcceptRole)
        box.addButton(QtWidgets.QMessageBox.Cancel)
        qexec(box)
        clicked = box.clickedButton()
        if clicked == b_all:
            pairs = ok + changed
        elif b_safe is not None and clicked == b_safe:
            pairs = ok
        else:
            return
        self._start_rollback([(it.path, bak) for it, bak in pairs])

    def _start_rollback(self, pairs):
        log.warning("Rolling back %d script(s) from their backups", len(pairs))
        thread = RollbackThread(pairs, self)
        thread.finished.connect(lambda t=thread: self._rollback_done(t))
        self._rollback_thread = thread
        self.set_running(self._running)          # disables the buttons
        thread.start()

    def _rollback_done(self, thread):
        self._rollback_thread = None
        failed = []
        for path, ok, message in thread.results:
            it = self.model.item_for_path(path)
            if ok:
                log.info("Rolled back %s", path)
                if it is not None:
                    it.status, it.saved, it.backup, it.duration = PENDING, None, None, None
                    it.message = message
                    it.refresh_stat()
            else:
                log.error("Roll-back FAILED %s: %s", path, message)
                failed.append("%s\n    %s" % (path, message))
                if it is not None:
                    it.message = message
            if it is not None:
                self.model.item_changed(path)
        thread.deleteLater()
        self.set_running(self._running)
        self.autosave()
        done = len(thread.results) - len(failed)
        log.info("Roll-back finished: %d restored, %d failed", done, len(failed))
        if failed:
            QtWidgets.QMessageBox.warning(
                self, "Roll Back", "%d restored, %d failed:\n\n%s" % (done, len(failed), "\n".join(failed[:15])))

    # ------------------------------------------------------------ stats
    def refresh_stats(self, paths=None):
        if self._stat_thread is not None:
            return
        paths = paths or [it.path for it in self.model.items]
        if not paths:
            return
        self.stats_btn.setEnabled(False)
        thread = StatThread(paths, self)
        thread.finished.connect(lambda t=thread: self._stats_done(t))
        self._stat_thread = thread
        thread.start()

    def _stats_done(self, thread):
        self._stat_thread = None
        self.stats_btn.setEnabled(not self._running)
        missing = 0
        for path, st in thread.stats.items():
            it = self.model.item_for_path(path)
            if it is None:
                continue
            if st is None:
                missing += 1
                it.size = it.mtime = None
            else:
                it.size, it.mtime = st
        thread.deleteLater()
        if self.model.items:
            self.model.dataChanged.emit(self.model.index(0, 4), self.model.index(len(self.model.items) - 1, 5))
        self._on_counts()
        if missing:
            log.warning("%d queued script(s) no longer exist on disk", missing)

    # ------------------------------------------------------------ files
    def _dialog_dir(self):
        d = self.settings.get("last_queue_dir")
        return d if d and os.path.isdir(d) else ""

    def load_dialog(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Queue", self._dialog_dir(), QUEUE_FILTER)
        if not path:
            return
        replace = True
        if self.model.items:
            box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, "Load Queue",
                                        "The queue already has %d scripts." % len(self.model.items),
                                        parent=self)
            b_replace = box.addButton("Replace", QtWidgets.QMessageBox.AcceptRole)
            b_append = box.addButton("Append", QtWidgets.QMessageBox.AcceptRole)
            box.addButton(QtWidgets.QMessageBox.Cancel)
            qexec(box)
            if box.clickedButton() == b_append:
                replace = False
            elif box.clickedButton() != b_replace:
                return
        self.load_file(path, replace=replace)

    def load_file(self, path, replace=True, quiet=False):
        try:
            items = queue_io.load_queue(path)
        except Exception as exc:
            if not quiet:
                QtWidgets.QMessageBox.warning(self, "Load Queue", "Cannot load %s:\n%s" % (path, exc))
            log.warning("Cannot load queue %s: %s", path, exc)
            return False
        if not replace:
            items = self.model.items + items
        self.model.set_items(items)
        self.settings.set("last_queue_dir", to_slash(os.path.dirname(path)))
        self.view.resizeColumnsToContents()
        self.view.setColumnWidth(0, 28)
        if not quiet:
            log.info("Loaded %d script(s) from %s", len(items), to_slash(path))
        self.refresh_stats()
        return True

    def save_dialog(self):
        start = os.path.join(self._dialog_dir(), "nukefixer_queue.json")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Queue", start, QUEUE_FILTER)
        if not path:
            return
        if path.lower().endswith(".txt"):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(it.path for it in self.model.items) + "\n")
        else:
            queue_io.save_queue(path, self.model.items)
        self.settings.set("last_queue_dir", to_slash(os.path.dirname(path)))
        log.info("Saved queue (%d scripts) to %s", len(self.model.items), to_slash(path))

    def export_dialog(self):
        start = os.path.join(self._dialog_dir(), "nukefixer_report.csv")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Report", start, "CSV (*.csv)")
        if path:
            queue_io.export_csv(path, self.model.items)
            log.info("Report written to %s", to_slash(path))

    def autosave(self):
        try:
            queue_io.save_queue(autosave_queue_path(), self.model.items)
        except (IOError, OSError) as exc:
            log.debug("Queue autosave failed: %s", exc)

    def restore_autosave(self):
        path = autosave_queue_path()
        if os.path.isfile(path):
            self.load_file(path, replace=True, quiet=True)
            if self.model.items:
                log.info("Restored queue from last session (%d scripts)", len(self.model.items))

    @property
    def busy(self):
        return self._rollback_thread is not None

    def shutdown(self):
        for t in (self._stat_thread, self._rollback_thread):
            if t is not None:
                t.wait(10000)
