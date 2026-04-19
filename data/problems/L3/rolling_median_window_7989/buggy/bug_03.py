from bisect import bisect_right, insort
from collections import deque

class RollingMedianWindow:
    def __init__(self, size):
        if not isinstance(size, int) or size <= 0:
            raise ValueError('size must be positive int')
        self.size = size
        self._q = deque()
        self._s = []

    def add(self, value):
        if len(self._q) == self.size:
            old = self._q.popleft()
            i = bisect_right(self._s, old) - 1
            del self._s[i]
        self._q.append(value)
        insort(self._s, value)
        return self.median()

    def median(self):
        n = len(self._s)
        if n == 0:
            raise ValueError('empty window')
        m = n // 2
        if n % 2:
            return self._s[m]
        return (self._s[m - 1] + self._s[m]) / 2.0

    def values(self):
        return list(self._q)
