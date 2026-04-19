from bisect import bisect_left, insort
from collections import deque

class RollingMedianWindow:
    def __init__(self, size):
        if type(size) is not int or size <= 0:
            raise ValueError('size must be positive int')
        self.size = size
        self._q = deque()
        self._s = []

    def add(self, value):
        if len(self._q) == self.size:
            old = self._q.popleft()
            i = bisect_left(self._s, old)
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
