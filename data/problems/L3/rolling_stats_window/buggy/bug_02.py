from collections import deque

class RollingWindowStats:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError('capacity must be positive')
        self.capacity = capacity
        self._data = deque()
        self._sum = 0

    def add(self, x):
        self._data.append(x)
        self._sum += x
        if len(self._data) > self.capacity:
            self._data.popleft()
        return len(self._data)

    def mean(self):
        if not self._data:
            raise ValueError('empty window')
        return self._sum / len(self._data)

    def minmax(self):
        if not self._data:
            raise ValueError('empty window')
        it = iter(self._data)
        first = next(it)
        lo = hi = first
        for v in it:
            if v < lo:
                lo = v
            if v > hi:
                hi = v
        return (lo, hi)

    def values(self):
        return list(self._data)

    def clear(self):
        self._data.clear()
        self._sum = 0
        return 0
