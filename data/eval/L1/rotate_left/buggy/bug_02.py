def rotate_left(items, k):
    n = len(items)
    if n == 0:
        return []
    shift = k
    return items[shift:] + items[:shift]
