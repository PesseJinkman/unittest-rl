class RollingWindow:
    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError('capacity must be positive')
        self.capacity = capacity
        self._items = []
        self._sum = 0

    def add(self, x):
        self._items.append(x)
        self._sum += x
        if len(self._items) > self.capacity:
            old = self._items.pop(0)
            self._sum -= old
        n = self.capacity if len(self._items) == self.capacity else len(self._items)
        return self._sum / n if self._items else None

    def stats(self):
        if not self._items:
            return {'count': 0, 'sum': 0, 'min': None, 'max': None, 'avg': None}
        n = self.capacity if len(self._items) == self.capacity else len(self._items)
        return {
            'count': len(self._items),
            'sum': self._sum,
            'min': min(self._items),
            'max': max(self._items),
            'avg': self._sum / n,
        }

    def snapshot(self):
        return list(self._items)
