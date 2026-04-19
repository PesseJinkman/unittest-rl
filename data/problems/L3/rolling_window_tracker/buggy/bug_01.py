from collections import deque

class RollingWindow:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError('capacity must be positive')
        self.capacity = capacity
        self._items = deque()
        self._sum = 0

    def add(self, x):
        self._items.append(x)
        self._sum += x
        if len(self._items) >= self.capacity:
            self._sum -= self._items.popleft()

    def total(self):
        return self._sum

    def average(self):
        return self._sum / len(self._items)

    def values(self):
        return list(self._items)

    def resize(self, new_capacity):
        if new_capacity <= 0:
            raise ValueError('capacity must be positive')
        self.capacity = new_capacity
        while len(self._items) > self.capacity:
            self._sum -= self._items.popleft()
        return len(self._items)
