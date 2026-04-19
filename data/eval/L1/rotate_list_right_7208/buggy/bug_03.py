def rotate_list_right(items, k):
    n = len(items)
    if n == 0:
        return []
    if k >= n:
        return items[:]
    shift = k % n
    if shift == 0:
        return items[:]
    return items[-shift:] + items[:-shift]
