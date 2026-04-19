def count_vowels(text):
    vowels = "aeiouAEIOUyY"
    total = 0
    for ch in text:
        if ch in vowels:
            total += 1
    return total
