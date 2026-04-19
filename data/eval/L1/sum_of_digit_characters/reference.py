def sum_of_digit_characters(text):
    total = 0
    for ch in text:
        if '0' <= ch <= '9':
            total += ord(ch) - ord('0')
    return total
