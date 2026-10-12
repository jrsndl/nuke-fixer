"""'Python Script' tab: editor + Load / Save / syntax check."""
import io
import logging
import os

from .qt import QtGui, QtWidgets, Signal
from .paths import scripts_dir, to_slash
from .widgets import hint_label

log = logging.getLogger("nukefixer.script")

HELP = ("Runs once per queued Nuke script, after it has been opened. Available: <b>nuke</b>, and "
        "<b>nf</b> with nf.file, nf.dry_run, nf.skip_save (set True to not save), nf.log('text'). "
        "Raise an exception to mark the script failed - it will not be saved. "
        "A backup copy is made before saving (Settings).")


class ScriptTab(QtWidgets.QWidget):
    scriptChanged = Signal()

    def __init__(self, settings, parent=None):
        super(ScriptTab, self).__init__(parent)
        self.settings = settings
        self._loaded_text = None

        self.load_btn = QtWidgets.QPushButton("Load...")
        self.load_btn.setToolTip("Load a python script from disk (starts in the scripts folder)")
        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_as_btn = QtWidgets.QPushButton("Save As...")
        self.check_btn = QtWidgets.QPushButton("Check Syntax")
        self.path_label = QtWidgets.QLabel("")
        self.path_label.setObjectName("hint")

        bar = QtWidgets.QHBoxLayout()
        for b in (self.load_btn, self.save_btn, self.save_as_btn, self.check_btn):
            bar.addWidget(b)
        bar.addWidget(self.path_label, 1)

        self.editor = QtWidgets.QPlainTextEdit()
        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        font.setPointSize(10)
        self.editor.setFont(font)
        self.editor.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.editor.setTabStopDistance(QtGui.QFontMetricsF(font).horizontalAdvance(" ") * 4)
        self.editor.setPlainText(settings.get("python_script"))

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(bar)
        lay.addWidget(hint_label(HELP))
        lay.addWidget(self.editor, 1)

        self.load_btn.clicked.connect(self.load)
        self.save_btn.clicked.connect(self.save)
        self.save_as_btn.clicked.connect(self.save_as)
        self.check_btn.clicked.connect(self.check_syntax_dialog)
        self.editor.textChanged.connect(self._on_text_changed)

        path = settings.get("python_script_path")
        if path and os.path.isfile(path):
            try:
                with io.open(path, "r", encoding="utf-8") as fh:
                    self._loaded_text = fh.read()
            except (IOError, OSError, UnicodeDecodeError):
                self._loaded_text = None
        self._update_label()

    # ------------------------------------------------------------------
    def text(self):
        return self.editor.toPlainText()

    def script_dir(self):
        path = self.settings.get("python_script_path")
        return os.path.dirname(path) if path and os.path.isfile(path) else None

    def check_syntax(self):
        """Return None if the script compiles, else an error message."""
        if not self.text().strip():
            return "The python script is empty."
        try:
            compile(self.text(), "<python script>", "exec")
        except SyntaxError as exc:
            return "Syntax error on line %s: %s\n%s" % (exc.lineno, exc.msg, (exc.text or "").rstrip())
        return None

    def check_syntax_dialog(self):
        err = self.check_syntax()
        if err:
            QtWidgets.QMessageBox.warning(self, "Python Script", err)
            if "line" in err:
                try:
                    line = int(err.split("line ")[1].split(":")[0])
                    block = self.editor.document().findBlockByLineNumber(line - 1)
                    cursor = self.editor.textCursor()
                    cursor.setPosition(block.position())
                    self.editor.setTextCursor(cursor)
                    self.editor.setFocus()
                except (IndexError, ValueError):
                    pass
        else:
            QtWidgets.QMessageBox.information(self, "Python Script", "No syntax errors found.")

    def _on_text_changed(self):
        self.settings.set("python_script", self.text())
        self._update_label()
        self.scriptChanged.emit()

    def _update_label(self):
        path = self.settings.get("python_script_path")
        if not path:
            self.path_label.setText("(unsaved script)")
            return
        modified = self._loaded_text is not None and self._loaded_text != self.text()
        self.path_label.setText(to_slash(path) + ("  (modified)" if modified else ""))

    def _start_dir(self):
        path = self.settings.get("python_script_path")
        if path and os.path.isdir(os.path.dirname(path)):
            return os.path.dirname(path)
        return scripts_dir()

    def load(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Python Script", scripts_dir() if not self.settings.get("python_script_path")
            else self._start_dir(), "Python (*.py);;All files (*)")
        if path:
            self.load_file(path)

    def load_file(self, path):
        try:
            with io.open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except (IOError, OSError, UnicodeDecodeError) as exc:
            QtWidgets.QMessageBox.warning(self, "Load Python Script", "Cannot read %s:\n%s" % (path, exc))
            return False
        self._loaded_text = text
        self.settings.set("python_script_path", to_slash(path))
        self.editor.setPlainText(text)
        log.info("Loaded python script %s", to_slash(path))
        return True

    def save(self):
        path = self.settings.get("python_script_path")
        if not path:
            return self.save_as()
        return self._write(path)

    def save_as(self):
        start = os.path.join(self._start_dir(), os.path.basename(self.settings.get("python_script_path") or "my_fix.py"))
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Python Script", start, "Python (*.py)")
        if not path:
            return False
        return self._write(path)

    def _write(self, path):
        try:
            with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(self.text())
        except (IOError, OSError) as exc:
            QtWidgets.QMessageBox.warning(self, "Save Python Script", "Cannot write %s:\n%s" % (path, exc))
            return False
        self._loaded_text = self.text()
        self.settings.set("python_script_path", to_slash(path))
        self._update_label()
        log.info("Saved python script %s", to_slash(path))
        return True
