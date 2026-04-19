def alternating_case(text):
    result = []
    make_upper = True
    for ch in text:
        if ch.isalpha():
            if make_upper:
                result.append(ch.upper())
                make_upper = False
            else:
                result.append(ch.lower())
        else:
            result.append(ch)
    return ''.join(result)
