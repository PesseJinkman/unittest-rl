def first_unique_char(s):
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    result = ""
    for ch in s:
        if counts[ch] == 1:
            result = ch
    return result
