def rotate_left(items, k):
    items = list(items)
    n = len(items)
    if n == 0:
        return []
    if n == 1:
        return items[:]
    shift = k % (n - 1)
    return items[shift:] + items[:shift]
