class WindowCounter:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError('capacity must be positive')
        self.capacity = capacity
        self._data = []
        self._sum = 0

    def add(self, x):
        self._data.append(x)
        self._sum += x
        if len(self._data) > self.capacity:
            removed = self._data.pop(0)
            self._sum -= removed
        return self._sum

    def total(self):
        return self._sum

    def average(self):
        if not self._data:
            raise ValueError('empty window')
        return self._sum / len(self._data)

    def last(self, n):
        if n < 0:
            raise ValueError('n must be non-negative')
        if n == 0:
            return []
        return list(self._data[-n:])
