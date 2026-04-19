def rotate_left(items, k):
    items = list(items)
    n = len(items)
    if n == 0:
        return []
    shift = k % n
    if shift == 0 and k != 0:
        shift = 1
    return items[shift:] + items[:shift]
