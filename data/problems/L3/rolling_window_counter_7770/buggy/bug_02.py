from collections import deque

class HitWindow:
    def __init__(self, window):
        if window <= 0:
            raise ValueError("window must be positive")
        self.window = window
        self._q = deque()
        self._total = 0
        self._latest = None

    def _evict(self, ts):
        cutoff = ts - self.window + 1
        while self._q and self._q[0][0] < cutoff:
            _, c = self._q.popleft()
            self._total -= c

    def add(self, ts, count=1):
        if count < 0:
            raise ValueError("count must be nonnegative")
        if self._latest is not None and ts <= self._latest:
            raise ValueError("timestamps must be increasing")
        self._latest = ts if self._latest is None or ts > self._latest else self._latest
        self._evict(ts)
        if count:
            if self._q and self._q[-1][0] == ts:
                old_ts, old_c = self._q[-1]
                self._q[-1] = (old_ts, old_c + count)
            else:
                self._q.append((ts, count))
            self._total += count
        return self._total

    def count(self, ts=None):
        if ts is None:
            return 0 if self._latest is None else self._total
        cutoff = ts - self.window + 1
        total = 0
        for t, c in self._q:
            if cutoff <= t <= ts:
                total += c
        return total
