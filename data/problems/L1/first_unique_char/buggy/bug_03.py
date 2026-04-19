def first_unique_char(s):
    seen = {}
    for ch in s:
        if ch not in seen:
            return ch
        seen[ch] = seen.get(ch, 0) + 1
    return ""
