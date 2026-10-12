"""NukeFixer - batch-apply a Python script to many Nuke scripts.

Package layout
--------------
Qt-free core (importable and testable without a GUI):
    paths        application / resource / user-data locations
    config       settings defaults and value coercion
    scanner      fast multi-threaded file search
    versions     version-regex parsing and first/last/all selection
    queue_io     queue items, save/load/export
    eta          progress + time-estimate tracking
    runner       NukePool: runs Nuke processes in parallel, crash/timeout safe
    nuke_runner  the script executed *inside* Nuke (never imported by the GUI)

Qt layer:
    qt, models, log_tab, find_tab, script_tab, queue_tab, settings_tab,
    main_window, app
"""

__version__ = "2.0.0"
APP_NAME = "NukeFixer"
