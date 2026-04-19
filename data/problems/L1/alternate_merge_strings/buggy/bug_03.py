def alternate_merge(a, b):
    result = []
    min_len = min(len(a), len(b))
    for i in range(min_len):
        result.append(a[i])
        result.append(b[i])
    if len(a) > min_len:
        result.append(a[min_len:])
    return ''.join(result)
