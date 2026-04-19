def rotate_left(items, k):
    """Return a new list rotated left by k positions."""
    n = len(items)
    if n == 0:
        return []
    k = k % n
    return items[k:] + items[:k]
