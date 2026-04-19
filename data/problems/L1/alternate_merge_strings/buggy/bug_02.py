def alternate_merge(a, b):
    result = []
    min_len = min(len(a), len(b))
    for i in range(min_len):
        result.append(a[i])
        result.append(b[i])
    return ''.join(result)
