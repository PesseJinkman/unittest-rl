class IntervalSet:
    def __init__(self):
        self._ranges = []

    def add(self, a, b):
        a, b = sorted((a, b))
        out = []
        placed = False
        for s, e in self._ranges:
            if e + 1 < a:
                out.append([s, e])
            elif b + 1 < s:
                if not placed:
                    out.append([a, b])
                    placed = True
                out.append([s, e])
            else:
                a, b = min(a, s), max(b, e)
        if not placed:
            out.append([a, b])
        self._ranges = out

    def remove(self, a, b):
        a, b = sorted((a, b))
        out = []
        for s, e in self._ranges:
            if e < a or s > b:
                out.append([s, e])
            else:
                if s < a:
                    out.append([s, a - 1])
                if e > b:
                    out.append([b + 1, e])
        self._ranges = out

    def contains(self, x):
        for s, e in self._ranges:
            if s <= x <= e:
                return True
            if x < s:
                return False
        return False

    def total_covered(self):
        return sum(e - s + 1 for s, e in self._ranges)

    def ranges(self):
        return self._ranges
