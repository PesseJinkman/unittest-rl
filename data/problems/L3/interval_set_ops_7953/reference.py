class IntervalSet:
    def __init__(self):
        self._ranges = []

    def add(self, start, end):
        if start > end:
            raise ValueError('start > end')
        res = []
        ns, ne = start, end
        placed = False
        for a, b in self._ranges:
            if b + 1 < ns:
                res.append((a, b))
            elif ne + 1 < a:
                if not placed:
                    res.append((ns, ne))
                    placed = True
                res.append((a, b))
            else:
                ns = min(ns, a)
                ne = max(ne, b)
        if not placed:
            res.append((ns, ne))
        self._ranges = res

    def remove(self, start, end):
        if start > end:
            raise ValueError('start > end')
        res = []
        for a, b in self._ranges:
            if b < start or a > end:
                res.append((a, b))
            else:
                if a < start:
                    res.append((a, start - 1))
                if b > end:
                    res.append((end + 1, b))
        self._ranges = res

    def contains(self, x):
        for a, b in self._ranges:
            if a <= x <= b:
                return True
            if x < a:
                return False
        return False

    def spans(self):
        return list(self._ranges)
