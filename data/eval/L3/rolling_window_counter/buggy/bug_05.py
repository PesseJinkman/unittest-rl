from collections import deque

class RollingWindowCounter:
    def __init__(self, window_size):
        if window_size <= 0:
            raise ValueError('window_size must be positive')
        self.window_size = window_size
        self._events = deque()
        self._total = 0
        self._last_ts = None

    def _expire(self, current_ts):
        cutoff = current_ts - self.window_size
        while self._events and self._events[0][0] < cutoff:
            ts, value = self._events.popleft()
            self._total -= value

    def add(self, ts, value=1):
        if value < 0:
            raise ValueError('value must be non-negative')
        if self._last_ts is not None and ts < self._last_ts:
            raise ValueError('timestamps must be non-decreasing')
        self._last_ts = ts
        self._events.append((ts, value))
        self._total += value
        self._expire(ts)
        return self._total

    def total(self):
        return self._total

    def count(self):
        return len(self._events)

    def snapshot(self):
        return (self.count(), self.total())
