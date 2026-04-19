def rotate_list_right(items, k):
    n = len(items)
    if n == 0:
        return []
    if n == 1:
        return list(items)
    shift = k % (n - 1)
    if shift == 0:
        return list(items)
    return list(items[-shift:]) + list(items[:-shift])
