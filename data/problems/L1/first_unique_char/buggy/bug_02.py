def first_unique_char(s):
    counts = {}
    for ch in s:
        key = ch.lower()
        counts[key] = counts.get(key, 0) + 1
    for ch in s:
        if counts[ch.lower()] == 1:
            return ch
    return ""
