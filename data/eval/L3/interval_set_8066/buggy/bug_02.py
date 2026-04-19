class IntervalSet:
    def __init__(self):
        self._iv = []

    def add(self, a, b):
        if a > b:
            a, b = b, a
        res = []
        placed = False
        for s, e in self._iv:
            if e < a - 1:
                res.append([s, e])
            elif b < s - 1:
                if not placed:
                    res.append([a, b])
                    placed = True
                res.append([s, e])
            else:
                a = min(a, s)
                b = max(b, e)
        if not placed:
            res.append([a, b])
        self._iv = res
        return self.intervals()

    def remove(self, a, b):
        if a > b:
            a, b = b, a
        res = []
        for s, e in self._iv:
            if e < a or s > b:
                res.append([s, e])
            else:
                if s < a:
                    res.append([s, a - 1])
                if e > b:
                    res.append([b, e])
        self._iv = res
        return self.intervals()

    def contains(self, x):
        for s, e in self._iv:
            if s <= x <= e:
                return True
            if x < s:
                return False
        return False

    def intervals(self):
        return [p[:] for p in self._iv]
