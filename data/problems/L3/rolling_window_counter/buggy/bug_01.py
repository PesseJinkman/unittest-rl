from collections import deque

class RollingCounter:
    def __init__(self, window_size):
        if window_size <= 0:
            raise ValueError('window_size must be positive')
        self.window_size = window_size
        self.events = deque()
        self._sum = 0
        self._last_add = None
        self._last_time = None

    def _prune(self, t):
        cutoff = t - self.window_size + 1
        while self.events and self.events[0][0] <= cutoff:
            _, v = self.events.popleft()
            self._sum -= v
        self._last_time = t

    def add(self, timestamp, value=1):
        if self._last_add is not None and timestamp < self._last_add:
            raise ValueError('timestamps must be non-decreasing')
        self._last_add = timestamp
        self.events.append((timestamp, value))
        self._sum += value
        if self._last_time is None or timestamp > self._last_time:
            self._prune(timestamp)
        return self._sum

    def total(self, now=None):
        if now is None:
            if self._last_add is None:
                return 0
            now = self._last_add
        if self._last_time is not None and now < self._last_time:
            raise ValueError('now cannot go backwards')
        self._prune(now)
        return self._sum

    def query(self, now):
        return self.total(now)
