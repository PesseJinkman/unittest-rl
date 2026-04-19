class IntervalCounterSet:
    def __init__(self):
        self.intervals = []

    def add(self, start, end):
        if start > end:
            start, end = end, start
        res = []
        placed = False
        for a, b in self.intervals:
            if b + 1 < start:
                res.append((a, b))
            elif end + 1 < a:
                if not placed:
                    res.append((start, end))
                    placed = True
                res.append((a, b))
            else:
                start = min(start, a)
                end = max(end, b)
        if not placed:
            res.append((start, end))
        self.intervals = res
        return list(self.intervals)

    def remove(self, start, end):
        if start > end:
            start, end = end, start
        res = []
        for a, b in self.intervals:
            if b < start or a > end:
                res.append((a, b))
            else:
                if a < start:
                    res.append((a, start - 1))
                if b > end:
                    res.append((end + 1, b))
        self.intervals = res
        return list(self.intervals)

    def contains(self, x):
        for a, b in self.intervals:
            if a <= x < b:
                return True
            if x < a:
                return False
        return False

    def total_covered(self):
        return sum(b - a + 1 for a, b in self.intervals)
