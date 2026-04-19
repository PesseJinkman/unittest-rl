from collections import deque

class WindowCounter:
    def __init__(self, window):
        if window <= 0:
            raise ValueError('window must be positive')
        self.window = window
        self.events = deque()
        self.current_sum = 0
        self.latest_ts = None

    def _expire(self, ts):
        cutoff = ts - self.window + 1
        while self.events and self.events[0][0] < cutoff:
            _, v = self.events.popleft()
            self.current_sum -= v

    def add(self, ts, value):
        if self.latest_ts is not None and ts < self.latest_ts:
            raise ValueError('timestamp out of order')
        self.latest_ts = ts
        self.events.append((ts, value))
        self.current_sum += value
        self._expire(ts)
        return self.current_sum

    def total(self, ts=None):
        if ts is None:
            if self.latest_ts is None:
                return 0
            ts = self.latest_ts
        self._expire(ts)
        return self.current_sum
