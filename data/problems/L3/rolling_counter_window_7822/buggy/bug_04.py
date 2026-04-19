from collections import deque

class RollingCounter:
    def __init__(self, window):
        if not isinstance(window, int) or window <= 0:
            raise ValueError('window must be positive int')
        self.window = window
        self.events = deque()
        self.counts = {}
        self.last_ts = None

    def _check_ts(self, ts):
        if not isinstance(ts, int):
            raise ValueError('timestamp must be int')
        if self.last_ts is not None and ts < self.last_ts:
            raise ValueError('timestamps must be non-decreasing')
        self.last_ts = ts

    def _expire(self, ts):
        cutoff = ts - self.window
        while self.events and self.events[0][0] <= cutoff:
            old_ts, key, amount = self.events.popleft()
            new_val = self.counts.get(key, 0) - amount
            if new_val:
                self.counts[key] = new_val
            elif key in self.counts:
                del self.counts[key]

    def add(self, ts, key, amount=1):
        self._check_ts(ts)
        if amount <= 0:
            raise ValueError('amount must be positive')
        self._expire(ts)
        self.events.append((ts, key, amount))
        self.counts[key] = self.counts.get(key, 0) + amount
        return sum(self.counts.values())

    def total(self, ts, key=None):
        self._check_ts(ts)
        self._expire(ts)
        if key is None:
            return sum(self.counts.values())
        return self.counts.get(key, 0)
