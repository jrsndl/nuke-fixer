"""Throughput-based time estimate for a run of parallel Nuke processes.

Finishing times with several Nuke processes are bursty, so the estimate blends
the recent completion rate (last ``window`` scripts) with the overall rate of
the run. The GUI recalculates it every few seconds and counts down between
recalculations, so the number is stable but keeps getting more precise.
"""
import time
from collections import deque


class EtaTracker(object):
    def __init__(self, window=30, recent_weight=0.7):
        self.window = window
        self.recent_weight = recent_weight
        self.reset(0)

    def reset(self, total, now=None):
        self.total = int(total)
        self.done = 0
        self.failed = 0
        self.t0 = time.time() if now is None else now
        self.stamps = deque(maxlen=self.window)

    def add_done(self, ok=True, now=None):
        now = time.time() if now is None else now
        self.done += 1
        if not ok:
            self.failed += 1
        self.stamps.append(now)

    @property
    def remaining(self):
        return max(0, self.total - self.done)

    def elapsed(self, now=None):
        return (time.time() if now is None else now) - self.t0

    def rate(self, now=None):
        """Scripts per second, or None while there is not enough data."""
        now = time.time() if now is None else now
        if self.done <= 0:
            return None
        overall = self.done / max(1e-6, now - self.t0)
        recent = None
        if len(self.stamps) >= 3:
            span = now - self.stamps[0]
            if span > 0:
                recent = (len(self.stamps) - 1) / span
        if recent is None:
            return overall
        return self.recent_weight * recent + (1 - self.recent_weight) * overall

    def eta(self, now=None):
        """Seconds left, or None if unknown."""
        if self.remaining == 0:
            return 0.0
        r = self.rate(now)
        if not r:
            return None
        return self.remaining / r
