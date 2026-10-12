"""NukeFixer - batch-apply a Python script to Nuke scripts.

Run from source:   python nuke_fixer.py
Build the exe:     build.bat   (PyInstaller, see NukeFixer.spec)
"""
import sys

from nukefixer.app import main

if __name__ == "__main__":
    sys.exit(main())
