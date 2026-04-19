def alternating_case(text):
    result = []
    make_upper = True
    for ch in text:
        if ch.isalpha():
            if make_upper:
                result.append(ch.upper())
            else:
                result.append(ch.lower())
                make_upper = not make_upper
        else:
            result.append(ch)
    return ''.join(result)
