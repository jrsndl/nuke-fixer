"""Minimal stand-in for the `nuke` module, used by the tests.

A "script" is a text file. scriptOpen() loads its text into ``state``,
scriptSave() writes ``state['text']`` back. Special words in the file let the
tests simulate trouble:
    CRASH    - the Nuke process dies while opening the script
    HANG     - opening the script never finishes
    BADLOAD  - scriptOpen raises (e.g. missing plugin)
    NOSAVE   - saving silently writes nothing
    SAMESAVE - saving writes the unmodified original back
"""
import os
import time

NUKE_VERSION_STRING = "fake-13.2"
state = {"path": None, "text": None}


class _Root(object):
    def name(self):
        return state["path"] or "Root"

    def setModified(self, value):
        state["modified"] = value


def root():
    return _Root()


def scriptOpen(path):
    with open(path) as fh:
        text = "".join(l for l in fh.read().splitlines(True) if not l.startswith("#root "))
    if "CRASH" in text:
        os._exit(3)
    if "HANG" in text:
        time.sleep(600)
    if "BADLOAD" in text:
        raise RuntimeError("unknown command: SomeMissingPlugin")
    state["path"], state["text"], state["original"] = path, text, text


def scriptSave(path=None):
    """Mimics the terminal-mode problem: returns without writing anything."""
    return False


def scriptSaveAs(filename=None, overwrite=-1):
    if "NOSAVE" in (state["text"] or ""):
        return                       # silently does nothing
    target = filename or state["path"]
    text = state["original"] if "SAMESAVE" in state["text"] else state["text"]
    with open(target, "w") as fh:
        fh.write("#root %s\n%s" % (target, text))
    state["path"] = target            # like Nuke: the root takes the new name


def scriptClear():
    state["path"], state["text"] = None, None


def allNodes(*args, **kwargs):
    return []
