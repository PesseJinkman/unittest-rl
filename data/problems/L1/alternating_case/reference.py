def alternating_case(text):
    result = []
    upper_next = True
    for ch in text:
        if ch.isalpha():
            if upper_next:
                result.append(ch.upper())
            else:
                result.append(ch.lower())
            upper_next = not upper_next
        else:
            result.append(ch)
    return ''.join(result)
