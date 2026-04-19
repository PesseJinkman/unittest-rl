def rotate_left(items, k):
    items = list(items)
    n = len(items)
    if n == 0:
        return []
    if k < 0:
        k = 0
    k = k % n
    return items[k:] + items[:k]
