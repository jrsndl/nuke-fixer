"""Application start-up."""
import io
import logging
import sys
import traceback

from .qt import PYSIDE_VERSION, QtCore, QtWidgets, Qt, qexec
from . import APP_NAME
from .log_tab import setup_logging
from .paths import images_dir, log_path, resource, settings_path, to_slash


def load_stylesheet():
    path = resource("nukefixer", "style.qss")
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            qss = fh.read()
    except (IOError, OSError):
        return ""
    return qss.replace("@IMAGES@", to_slash(images_dir()))


def _install_excepthook():
    """Log unexpected exceptions instead of letting Qt abort the process."""
    log = logging.getLogger("nukefixer")

    def hook(exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        log.error("Unexpected error:\n%s", "".join(traceback.format_exception(exc_type, exc, tb)))
        app = QtWidgets.QApplication.instance()
        if app is not None:
            QtWidgets.QMessageBox.critical(None, APP_NAME, "Unexpected error (details in the Log tab and "
                                           "log file):\n\n%s: %s" % (exc_type.__name__, exc))
    sys.excepthook = hook


def main(argv=None):
    argv = sys.argv if argv is None else argv
    if PYSIDE_VERSION == 2:
        QtCore.QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QtCore.QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setStyleSheet(load_stylesheet())

    # import late: Settings needs a QCoreApplication for QSettings
    from .settings import Settings
    from .main_window import MainWindow

    settings = Settings(settings_path())
    setup_logging(log_path(), settings.get("log_level_file"), settings.get("log_max_kb"))
    _install_excepthook()

    window = MainWindow(settings)
    window.show()
    return qexec(app)


if __name__ == "__main__":
    sys.exit(main())
