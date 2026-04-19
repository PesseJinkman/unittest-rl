from bisect import bisect_right, insort
from collections import deque

class RollingMedian:
    def __init__(self, size):
        if size <= 0:
            raise ValueError('size must be positive')
        self.size = size
        self._queue = deque()
        self._sorted = []

    def add(self, value):
        if len(self._queue) == self.size:
            old = self._queue.popleft()
            i = bisect_right(self._sorted, old)
            del self._sorted[i - 1]
        self._queue.append(value)
        insort(self._sorted, value)
        n = len(self._sorted)
        m = n // 2
        if n % 2:
            return self._sorted[m]
        return (self._sorted[m - 1] + self._sorted[m]) / 2.0

    def snapshot(self):
        return list(self._queue)
