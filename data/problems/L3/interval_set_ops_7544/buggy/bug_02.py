class IntervalSet:
    def __init__(self):
        self._iv = []

    def add(self, start, end):
        if start > end:
            start, end = end, start
        res = []
        placed = False
        for a, b in self._iv:
            if b + 1 < start:
                res.append([a, b])
            elif end + 1 < a:
                if not placed:
                    res.append([start, end])
                    placed = True
                res.append([a, b])
            else:
                start = min(start, a)
                end = max(end, b)
        if not placed:
            res.append([start, end])
        self._iv = res

    def remove(self, start, end):
        if start > end:
            start, end = end, start
        res = []
        for a, b in self._iv:
            if b < start or a > end:
                res.append([a, b])
            else:
                if a < start:
                    res.append([a, start - 1])
                if b > end:
                    res.append([end, b])
        self._iv = res

    def contains(self, x):
        for a, b in self._iv:
            if a <= x <= b:
                return True
            if x < a:
                return False
        return False

    def intervals(self):
        return [p[:] for p in self._iv]
