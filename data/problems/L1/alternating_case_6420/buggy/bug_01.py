def alternating_case(text):
    result = []
    make_upper = True
    for ch in text:
        if ch.isalpha():
            if make_upper:
                result.append(ch.upper())
            else:
                result.append(ch.lower())
        else:
            result.append(ch)
        make_upper = not make_upper
    return ''.join(result)
