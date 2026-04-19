from collections import deque

class RollingCounter:
    def __init__(self, window):
        if not isinstance(window, int) or window <= 0:
            raise ValueError('window must be positive int')
        self.window = window
        self._q = deque()
        self._sum = 0
        self._latest = None

    def _advance(self, ts):
        if not isinstance(ts, int):
            raise TypeError('timestamp must be int')
        if self._latest is not None and ts < self._latest:
            raise ValueError('timestamp moved backwards')
        self._latest = ts
        cutoff = ts - self.window + 1
        while self._q and self._q[0][0] < cutoff:
            _, v = self._q.popleft()
            self._sum -= v

    def hit(self, ts, value=1):
        if not isinstance(value, int) or value < 0:
            raise ValueError('value must be non-negative int')
        self._advance(ts)
        if value:
            if self._q and self._q[-1][0] == ts:
                old_ts, old_v = self._q[-1]
                self._q[-1] = (old_ts, old_v + value)
            else:
                self._q.append((ts, value))
            self._sum += value
        return self._sum

    def total(self, ts=None):
        if self._latest is None:
            return 0
        if ts is None:
            ts = self._latest
        self._advance(ts - 1)
        return self._sum
