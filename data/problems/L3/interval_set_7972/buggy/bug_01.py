class IntervalSet:
    def __init__(self):
        self._spans = []

    def add(self, start, end):
        if start > end:
            start, end = end, start
        out = []
        placed = False
        for a, b in self._spans:
            if b < start:
                out.append((a, b))
            elif end < a:
                if not placed:
                    out.append((start, end))
                    placed = True
                out.append((a, b))
            else:
                start = min(start, a)
                end = max(end, b)
        if not placed:
            out.append((start, end))
        self._spans = out

    def remove(self, start, end):
        if start > end:
            start, end = end, start
        out = []
        for a, b in self._spans:
            if b < start or a > end:
                out.append((a, b))
            else:
                if a < start:
                    out.append((a, start - 1))
                if b > end:
                    out.append((end + 1, b))
        self._spans = out

    def contains(self, x):
        for a, b in self._spans:
            if a <= x <= b:
                return True
            if x < a:
                return False
        return False

    def spans(self):
        return list(self._spans)
