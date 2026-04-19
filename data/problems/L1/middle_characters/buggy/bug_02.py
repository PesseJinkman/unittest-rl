def middle_characters(s):
    n = len(s)
    if n == 0:
        return ""
    mid = n // 2
    if n % 2 == 1:
        return s[mid - 1:mid + 1]
    return s[mid - 1:mid + 1]
