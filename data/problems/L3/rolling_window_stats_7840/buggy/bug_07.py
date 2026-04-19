from collections import deque

class RollingWindow:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError('capacity must be positive')
        self.capacity = capacity
        self._data = deque()
        self._sum = 0
        self._minq = deque()
        self._maxq = deque()

    def _add_minmax(self, x):
        while self._minq and self._minq[-1] > x:
            self._minq.pop()
        self._minq.append(x)
        while self._maxq and self._maxq[-1] < x:
            self._maxq.pop()
        self._maxq.append(x)

    def _remove_minmax(self, x):
        if self._minq and self._minq[0] == x:
            self._minq.popleft()
        if self._maxq and self._maxq[0] == x:
            self._maxq.popleft()

    def push(self, x):
        self._data.append(x)
        self._sum += x
        self._add_minmax(x)
        if len(self._data) > self.capacity:
            old = self._data.popleft()
            self._sum -= old
            self._remove_minmax(old)
        return len(self._data)

    def pop_oldest(self):
        if not self._data:
            raise IndexError('pop from empty window')
        old = self._data.popleft()
        self._sum -= old
        self._remove_minmax(old)
        return old

    def stats(self):
        if not self._data:
            return {'count': 0, 'sum': 0, 'min': None, 'max': None, 'avg': 0.0}
        count = len(self._data)
        return {
            'count': count,
            'sum': self._sum,
            'min': self._minq[0],
            'max': self._maxq[0],
            'avg': self._sum / count,
        }
