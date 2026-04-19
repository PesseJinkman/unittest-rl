def sum_of_digit_characters(text):
    total = 0
    seen_digit = False
    for ch in text:
        if '0' <= ch <= '9':
            total += ord(ch) - ord('0')
            seen_digit = True
        elif seen_digit:
            break
    return total
