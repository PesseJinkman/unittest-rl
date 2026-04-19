from bisect import bisect_right, insort
from collections import deque

class RollingMedian:
    def __init__(self, window_size):
        if not isinstance(window_size, int) or window_size <= 0:
            raise ValueError('window_size must be positive int')
        self.window_size = window_size
        self._queue = deque()
        self._sorted = []

    def add(self, x):
        self._queue.append(x)
        insort(self._sorted, x)
        if len(self._queue) > self.window_size:
            old = self._queue.popleft()
            i = bisect_right(self._sorted, old) - 1
            del self._sorted[i]
        return self.median()

    def median(self):
        n = len(self._sorted)
        if n == 0:
            raise IndexError('median of empty window')
        mid = n // 2
        if n % 2:
            return self._sorted[mid]
        return (self._sorted[mid - 1] + self._sorted[mid]) / 2.0

    def clear(self):
        self._queue.clear()
        self._sorted.clear()
