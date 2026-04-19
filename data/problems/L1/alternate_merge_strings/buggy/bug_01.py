def alternate_merge(a, b):
    result = []
    max_len = max(len(a), len(b))
    for i in range(max_len):
        if i < len(b):
            result.append(b[i])
        if i < len(a):
            result.append(a[i])
    return ''.join(result)
