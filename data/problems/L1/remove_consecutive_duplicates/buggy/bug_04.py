def remove_consecutive_duplicates(items):
    result = []
    for i in range(1, len(items)):
        if items[i] != items[i - 1]:
            result.append(items[i])
    return result
