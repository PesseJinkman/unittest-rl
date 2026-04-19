from collections import deque

class RollingCounter:
    def __init__(self, window_size):
        if window_size <= 0:
            raise ValueError('window_size must be > 0')
        self.window_size = window_size
        self._events = deque()
        self._total = 0
        self._last_ts = None

    def _prune(self, ts):
        cutoff = ts - self.window_size + 1
        while self._events and self._events[0][0] < cutoff:
            _, delta = self._events.popleft()
            self._total -= delta

    def add(self, ts, delta=1):
        if self._last_ts is not None and ts < self._last_ts:
            raise ValueError('timestamps must be non-decreasing')
        self._prune(ts)
        self._events.append((ts, delta))
        self._total += delta
        self._last_ts = ts
        return self._total

    def total_at(self, ts):
        if self._last_ts is not None and ts < self._last_ts:
            raise ValueError('query timestamp too old')
        self._prune(ts)
        return self._total

    def reset(self):
        self._events.clear()
        self._total = 0
