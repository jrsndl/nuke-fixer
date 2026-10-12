"""QSettings-backed settings with typed values, defaults and change signal."""
import logging

from .qt import QtCore, Signal
from . import config

log = logging.getLogger("nukefixer.settings")

LEGACY_KEYS = ("apply_first", "apply_last", "apply_all", "select_all_none",
               "regex", "all", "first", "last")


class Settings(QtCore.QObject):
    changed = Signal(str, object)

    def __init__(self, path, parent=None):
        super(Settings, self).__init__(parent)
        self.path = path
        self.qs = QtCore.QSettings(path, QtCore.QSettings.IniFormat)
        self.qs.setFallbacksEnabled(False)
        self.values = {}
        self.load()

    def load(self):
        for key in config.DEFAULTS:
            fallback = config.default(key)
            try:
                self.values[key] = config.coerce(self.qs.value(key), fallback)
            except Exception as exc:      # never let one bad key reset everything
                log.warning("Bad value for setting %s (%s) - using default", key, exc)
                self.values[key] = fallback

        if self.qs.value("version_mode") is None:
            legacy = config.legacy_version_mode(self.qs.value("apply_first"),
                                                self.qs.value("apply_last"),
                                                self.qs.value("apply_all"))
            if legacy:
                self.values["version_mode"] = legacy
        if self.values["version_mode"] not in config.VERSION_MODES:
            self.values["version_mode"] = "last"
        for key in ("log_level_file", "log_level_view"):
            if self.values[key] not in config.LOG_LEVELS:
                self.values[key] = "INFO"
        if not self.values["python_script"].strip():
            self.values["python_script"] = config.DEFAULT_SCRIPT

    def get(self, key):
        return self.values[key]

    def set(self, key, value):
        if self.values.get(key) == value:
            return
        self.values[key] = value
        self.qs.setValue(key, value)
        self.changed.emit(key, value)

    def save(self):
        for key, value in self.values.items():
            self.qs.setValue(key, value)
        for key in LEGACY_KEYS:
            self.qs.remove(key)
        self.qs.sync()
        if self.qs.status() != QtCore.QSettings.NoError:
            log.error("Could not write settings to %s", self.path)
            return False
        return True

    def restore_defaults(self, keys):
        for key in keys:
            self.set(key, config.default(key))
