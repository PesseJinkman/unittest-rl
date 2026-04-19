def rotate_list_right(items, k):
    if not items:
        return []
    n = len(items)
    shift = k % n
    if shift == 0:
        return items[:]
    return items[-shift:] + items[:-shift-1]
