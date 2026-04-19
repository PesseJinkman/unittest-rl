def rotate_list_right(items, k):
    if not items:
        return []
    shift = k
    if shift == 0:
        return items[:]
    return items[-shift:] + items[:-shift]
