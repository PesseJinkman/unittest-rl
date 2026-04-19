from collections import deque

class RollingCounter:
    def __init__(self, window):
        if not isinstance(window, int):
            raise ValueError('window must be an int')
        self.window = window
        self._q = deque()
        self._sum = 0
        self._last_time = None

    def _evict(self, end):
        cutoff = end - self.window + 1
        while self._q and self._q[0][0] < cutoff:
            _, v = self._q.popleft()
            self._sum -= v

    def add(self, t, value=1):
        if not isinstance(t, int):
            raise TypeError('t must be int')
        if not isinstance(value, int) or value < 0:
            raise ValueError('value must be a non-negative int')
        if self._last_time is not None and t < self._last_time:
            raise ValueError('time must be non-decreasing')
        self._last_time = t
        if value:
            self._q.append((t, value))
            self._sum += value
        self._evict(t)
        return self._sum

    def total(self, now=None):
        if now is None:
            if self._last_time is None:
                return 0
            end = self._last_time
        else:
            if not isinstance(now, int):
                raise TypeError('now must be int')
            if self._last_time is not None and now < self._last_time:
                raise ValueError('now cannot go backwards')
            end = now
        self._evict(end)
        return self._sum
