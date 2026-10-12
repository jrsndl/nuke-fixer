"""Version parsing and first / last / all selection per folder (Qt-free)."""
import os
import re
from collections import defaultdict


class Candidate(object):
    """A found file plus the version string the regex extracted."""
    __slots__ = ("file", "version")

    def __init__(self, found_file, version):
        self.file = found_file
        self.version = version

    @property
    def path(self):
        return self.file.path


def compile_version_regex(text, ignore_case=os.name == "nt"):
    """Return (compiled_regex, error_message)."""
    if not text or not text.strip():
        return None, "Version regex is empty."
    try:
        rx = re.compile(text, re.IGNORECASE if ignore_case else 0)
    except re.error as exc:
        return None, "Invalid version regex: %s" % exc
    if rx.groups < 1:
        return None, ("Version regex needs a capture group around the version "
                      "number, e.g. _v(\\d+)\\.nk$")
    return rx, None


def version_key(text):
    """Numeric versions sort numerically (v99 < v100); anything else as text."""
    text = text or ""
    digits = re.sub(r"\D", "", text)
    if digits and digits == text.lstrip("vV"):
        return (0, int(digits), text)
    return (1, 0, text.lower())


def select_versions(files, rx, mode="last"):
    """Group ``files`` by folder and pick the first / last / all versions.

    Returns (candidates, unmatched_count). Files the regex doesn't match are
    counted, not selected. Folders with no matching file are simply skipped.
    """
    if mode not in ("first", "last", "all"):
        raise ValueError("mode must be first, last or all")
    groups = defaultdict(list)
    unmatched = 0
    for f in files:
        m = rx.search(f.name)
        if not m or m.group(1) is None:
            unmatched += 1
            continue
        version = m.group(1)
        groups[f.folder].append((version_key(version), f.name.lower(), version, f))

    out = []
    for folder in sorted(groups, key=str.lower):
        items = sorted(groups[folder], key=lambda t: (t[0], t[1]))
        if mode == "first":
            items = items[:1]
        elif mode == "last":
            items = items[-1:]
        out.extend(Candidate(f, version) for _, _, version, f in items)
    return out, unmatched
