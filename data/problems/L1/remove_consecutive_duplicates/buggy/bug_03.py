def remove_consecutive_duplicates(items):
    if not items:
        return []
    result = []
    for i in range(len(items) - 1):
        if items[i] != items[i + 1]:
            result.append(items[i + 1])
    if len(items) == 1:
        result.append(items[0])
    return result
