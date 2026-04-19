def alternating_case(text):
    result = []
    upper_next = True
    for ch in text:
        if ch.isalpha():
            if upper_next:
                result.append(ch.lower())
            else:
                result.append(ch.upper())
            upper_next = not upper_next
        else:
            result.append(ch)
    return ''.join(result)
