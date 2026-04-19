def rotate_right(nums, k):
    items = list(nums)
    n = len(items)
    if n == 0:
        return []
    shift = k % n
    if shift <= 1:
        return items[:]
    return items[-shift:] + items[:-shift]
