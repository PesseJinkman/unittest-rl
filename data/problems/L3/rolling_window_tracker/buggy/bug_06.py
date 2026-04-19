class RollingWindow:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError('capacity must be positive')
        self.capacity = capacity
        self._items = []
        self._history = []

    def add(self, x):
        self._items.append(x)
        self._history.append(x)
        if len(self._items) > self.capacity:
            self._items.pop(0)

    def total(self):
        return sum(self._history)

    def average(self):
        return self.total() / len(self._items)

    def values(self):
        return list(self._items)

    def resize(self, new_capacity):
        if new_capacity <= 0:
            raise ValueError('capacity must be positive')
        self.capacity = new_capacity
        while len(self._items) > self.capacity:
            self._items.pop(0)
        return len(self._items)
