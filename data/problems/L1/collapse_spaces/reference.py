def collapse_spaces(text):
    result = []
    prev_space = False
    for ch in text:
        if ch == ' ':
            if not prev_space:
                result.append(' ')
            prev_space = True
        else:
            result.append(ch)
            prev_space = False
    return ''.join(result)
