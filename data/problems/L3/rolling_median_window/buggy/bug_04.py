from collections import deque

class RollingMedian:
    def __init__(self, size):
        if not isinstance(size, int) or size <= 0:
            raise ValueError('size must be a positive int')
        self.size = size
        self._items = deque()

    def __len__(self):
        return len(self._items)

    def add(self, x):
        self._items.append(x)
        if len(self._items) > self.size:
            self._items.popleft()
        return self.median()

    def median(self):
        if not self._items:
            raise ValueError('median of empty window')
        data = sorted(self._items)
        n = len(data)
        mid = n // 2
        if n % 2:
            return data[mid - 1]
        return (data[mid - 1] + data[mid]) / 2.0
