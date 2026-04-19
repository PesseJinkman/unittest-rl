def sum_of_digit_characters(text):
    total = 0
    current = ''
    for ch in text:
        if '0' <= ch <= '9':
            current += ch
        else:
            if current:
                total += int(current)
                current = ''
    if current:
        total += int(current)
    return total
