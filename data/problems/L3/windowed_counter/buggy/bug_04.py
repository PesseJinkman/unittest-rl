class WindowCounter:
    def __init__(self, window):
        if not isinstance(window, int) or window <= 0:
            raise ValueError('window must be positive int')
        self.window = window
        self.tick = 0
        self.total_sum = 0
        self.buckets = {}

    def _prune(self):
        cutoff = self.tick - self.window + 1
        stale = [t for t in self.buckets if t < cutoff]
        for t in stale:
            self.total_sum -= self.buckets.pop(t)

    def add(self, value=1):
        if not isinstance(value, int) or value <= 0:
            raise ValueError('value must be non-negative int')
        self.buckets[self.tick] = self.buckets.get(self.tick, 0) + value
        self.total_sum += value
        self._prune()
        return self.total_sum

    def advance(self, steps=1):
        if not isinstance(steps, int) or steps <= 0:
            raise ValueError('steps must be positive int')
        self.tick += steps
        self._prune()
        return self.total_sum

    def total(self):
        self._prune()
        return self.total_sum
