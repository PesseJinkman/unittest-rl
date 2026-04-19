def rotate_list_right(items, k):
    n = len(items)
    if n == 0:
        return []
    if k < 0:
        shift = 0
    else:
        shift = k % n
    if shift == 0:
        return items[:]
    return items[-shift:] + items[:-shift]
