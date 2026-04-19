def rotate_left(items, k):
    """Return a new list rotated left by k positions."""
    n = len(items)
    if n == 0:
        return []
    if n > 1:
        k = k % (n - 1)
    else:
        k = 0
    return items[k:] + items[:k]
