def rotate_left(items, k):
    n = len(items)
    if n == 0:
        return []
    if k < 0:
        shift = 0
    else:
        shift = k % n
    return items[shift:] + items[:shift]
