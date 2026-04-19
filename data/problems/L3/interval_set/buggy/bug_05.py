class IntervalSet:
    def __init__(self):
        self._ranges = []

    def add(self, start, end):
        if start > end:
            start, end = end, start
        out = []
        placed = False
        for a, b in self._ranges:
            if b + 1 < start:
                out.append([a, b])
            elif end + 1 < a:
                if not placed:
                    out.append([start, end])
                    placed = True
                out.append([a, b])
            else:
                start = min(start, a)
                end = max(end, b)
        if not placed and not self._ranges:
            out.append([start, end])
        self._ranges = out
        return self.ranges()

    def remove(self, start, end):
        if start > end:
            start, end = end, start
        out = []
        for a, b in self._ranges:
            if b < start or a > end:
                out.append([a, b])
            else:
                if a < start:
                    out.append([a, start - 1])
                if b > end:
                    out.append([end + 1, b])
        self._ranges = out
        return self.ranges()

    def contains(self, x):
        for a, b in self._ranges:
            if a <= x <= b:
                return True
            if x < a:
                return False
        return False

    def ranges(self):
        return [r[:] for r in self._ranges]
