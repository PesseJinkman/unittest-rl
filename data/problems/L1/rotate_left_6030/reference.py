def rotate_left(items, k):
    items = list(items)
    n = len(items)
    if n == 0:
        return []
    k = k % n
    return items[k:] + items[:k]
