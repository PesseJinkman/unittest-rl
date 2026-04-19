def rotate_list_right(items, k):
    n = len(items)
    if n == 0:
        return []
    shift = k % n
    if shift == 0:
        return list(items)
    return list(items[-shift:]) + list(items[:-shift - 1])
