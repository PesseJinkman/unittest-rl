def rotate_right(items, k):
    items = list(items)
    n = len(items)
    if n == 0:
        return []
    k = abs(k) % n
    if k == 0:
        return items[:]
    return items[-k:] + items[:-k]
