class IntervalSet:
    def __init__(self):
        self._spans = []

    def add(self, start, end):
        if start >= end:
            return
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
        if start >= end:
            return
        out = []
        for a, b in self._spans:
            if b <= start or a >= end:
                out.append((a, b))
            else:
                if a <= start:
                    out.append((a, start))
                if end < b:
                    out.append((end, b))
        self._spans = out

    def contains(self, x):
        for a, b in self._spans:
            if a <= x < b:
                return True
            if x < a:
                return False
        return False

    def spans(self):
        return list(self._spans)


def exercise_interval_set(ops):
    s = IntervalSet()
    out = []
    for op in ops:
        name = op[0]
        if name == 'add':
            s.add(op[1], op[2])
            out.append(None)
        elif name == 'remove':
            s.remove(op[1], op[2])
            out.append(None)
        elif name == 'contains':
            out.append(s.contains(op[1]))
        elif name == 'spans':
            out.append(s.spans())
        else:
            raise ValueError('unknown op')
    return out
