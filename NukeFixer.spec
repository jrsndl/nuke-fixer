# -*- mode: python ; coding: utf-8 -*-
# PyInstaller build:  pyinstaller --noconfirm NukeFixer.spec   (or run build.bat)

datas = [
    ("nukefixer/nuke_runner.py", "nukefixer"),   # executed by Nuke, must be a real file
    ("nukefixer/style.qss", "nukefixer"),
    ("images", "images"),
    ("scripts", "scripts"),
]

a = Analysis(
    ["nuke_fixer.py"],
    pathex=[],
    datas=datas,
    hiddenimports=[],
    excludes=["tkinter", "unittest", "pydoc"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NukeFixer",
    console=False,
    icon=None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="NukeFixer")
