def alternate_merge(a, b):
    result = []
    i = 0
    j = 0
    take_from_a = True

    while i < len(a) and j < len(b):
        if take_from_a:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
        take_from_a = not take_from_a

    if i < len(a):
        result.append(a[i:])
    if j < len(b):
        result.append(b[j:])

    return ''.join(result)
