class IntervalSet:
    def __init__(self):
        self._iv = []

    def add(self, start, end):
        if start >= end:
            return
        res = []
        i = 0
        while i < len(self._iv) and self._iv[i][1] < start:
            res.append(self._iv[i])
            i += 1
        ns, ne = start, end
        while i < len(self._iv) and self._iv[i][0] <= end:
            ns = min(ns, self._iv[i][0])
            ne = max(ne, self._iv[i][1])
            i += 1
        res.append([ns, ne])
        res.extend(self._iv[i:])
        self._iv = res

    def remove(self, start, end):
        if start > end:
            return
        res = []
        for a, b in self._iv:
            if b <= start or a >= end:
                res.append([a, b])
            else:
                if a < start:
                    res.append([a, start])
                if b > end:
                    res.append([end, b])
        self._iv = res

    def contains(self, x):
        for a, b in self._iv:
            if a <= x < b:
                return True
            if x < a:
                return False
        return False

    def intervals(self):
        return [iv[:] for iv in self._iv]
