from collections import deque

class RollingStats:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError('capacity must be positive')
        self.capacity = capacity
        self._q = deque()
        self._sum = 0.0

    def add(self, x):
        if len(self._q) == self.capacity:
            self._sum -= self._q.popleft()
        self._q.append(x)
        self._sum += x
        return len(self._q)

    def mean(self):
        if not self._q:
            raise IndexError('empty window')
        return self._sum / len(self._q)

    def min(self):
        if not self._q:
            raise IndexError('empty window')
        return min(self._q)

    def max(self):
        if not self._q:
            raise IndexError('empty window')
        return max(self._q)

    def values(self):
        return list(reversed(self._q))

    def clear(self):
        self._q.clear()
        self._sum = 0.0
        return 0
