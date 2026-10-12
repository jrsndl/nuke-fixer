"""Pretends to be `Nuke -t script.py args...` for the tests.

FAKE_NUKE_FAIL_START=1 makes it exit immediately like a licence failure.
"""
import os
import runpy
import sys

if os.environ.get("FAKE_NUKE_FAIL_START"):
    print("Nuke: no license available (fake)")
    sys.exit(100)

args = [a for a in sys.argv[1:] if a not in ("-t", "-ti", "-q")]
script, rest = args[0], args[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [script] + rest
print("Fake Nuke starting")
runpy.run_path(script, run_name="__main__")
