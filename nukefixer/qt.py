"""Qt binding shim: PySide6 preferred, PySide2 (Qt 5.15) still supported."""
try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtGui import QAction, QShortcut
    PYSIDE_VERSION = 6
except ImportError:  # pragma: no cover - depends on installed binding
    from PySide2 import QtCore, QtGui, QtWidgets
    from PySide2.QtWidgets import QAction, QShortcut
    PYSIDE_VERSION = 2

Qt = QtCore.Qt
Signal = QtCore.Signal
Slot = QtCore.Slot


def qexec(obj, *args):
    """exec() / exec_() across bindings."""
    fn = getattr(obj, "exec", None) or getattr(obj, "exec_")
    return fn(*args)


def enum_value(value):
    """Qt enums are Python enums in PySide6 and ints in PySide2."""
    return getattr(value, "value", value)


def is_checked(value):
    try:
        return int(enum_value(value)) == int(enum_value(Qt.Checked))
    except (TypeError, ValueError):
        return False


__all__ = ["QtCore", "QtGui", "QtWidgets", "QAction", "QShortcut", "Qt", "Signal",
           "Slot", "qexec", "enum_value", "is_checked", "PYSIDE_VERSION"]
