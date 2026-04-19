def count_vowels(text):
    vowels = "aeiouAEIOU"
    total = 0
    for ch in text[:-1]:
        if ch in vowels:
            total += 1
    return total
