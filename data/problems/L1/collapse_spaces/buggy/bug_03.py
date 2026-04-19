def collapse_spaces(text):
    result = []
    i = 0
    n = len(text)
    while i < n:
        if i + 1 < n and text[i] == ' ' and text[i + 1] == ' ':
            result.append(' ')
            i += 2
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)
