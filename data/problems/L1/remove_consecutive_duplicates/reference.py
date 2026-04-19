def remove_consecutive_duplicates(items):
    result = []
    for item in items:
        if not result or item != result[-1]:
            result.append(item)
    return result
