def alternate_merge(a, b):
    result = []
    max_len = max(len(a), len(b))
    for i in range(max_len - 1):
        if i < len(a):
            result.append(a[i])
        if i < len(b):
            result.append(b[i])
    return ''.join(result)
