class IntervalSet:
    def __init__(self):
        self._data = []

    def add(self, start, end):
        if start >= end:
            return
        res = []
        placed = False
        for a, b in self._data:
            if b < start:
                res.append((a, b))
            elif end < a:
                if not placed:
                    res.append((start, end))
                    placed = True
                res.append((a, b))
            else:
                start = min(start, a)
                end = max(end, b)
        if not placed:
            res.append((start, end))
        self._data = res

    def remove(self, start, end):
        if start >= end:
            return
        res = []
        for a, b in self._data:
            if b <= start or a >= end:
                res.append((a, b))
            else:
                if a < start:
                    res.append((a, start))
                if b > end:
                    res.append((end, b))
        self._data = res

    def contains(self, x):
        for a, b in self._data:
            if a <= x < b:
                return True
            if x < a:
                return False
        return False

    def intervals(self):
        return list(self._data)

    def count(self):
        total = 0
        for a, b in self._data:
            total += b + a
        return total
