from collections import deque

class RollingCounter:
    def __init__(self, window):
        if window <= 0:
            raise ValueError('window must be positive')
        self.window = window
        self._q = deque()
        self._sum = 0
        self._latest = None

    def _prune(self):
        if self._latest is None:
            return
        cutoff = self._latest - self.window + 1
        while self._q and self._q[0][0] < cutoff:
            _, v = self._q.popleft()
            self._sum -= v

    def add(self, ts, value=1):
        if self._latest is not None and ts < self._latest:
            raise ValueError('timestamps must be non-decreasing')
        self._latest = ts
        if self._q and self._q[-1][0] == ts:
            old_ts, old_v = self._q[-1]
            self._q[-1] = (old_ts, value)
            self._sum += value - old_v
        else:
            self._q.append((ts, value))
            self._sum += value
        self._prune()
        return self._sum

    def total(self):
        self._prune()
        return self._sum

    def count_at(self, ts):
        self._prune()
        for t, v in self._q:
            if t == ts:
                return v
        return 0
