def count_vowels(text):
    vowels = set('aeiou')
    total = 0
    for ch in text.lower():
        if ch in vowels:
            total += 1
    return total
