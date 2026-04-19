def count_vowels(text):
    vowels = "aeiouAEIOUyY"
    count = 0
    for ch in text:
        if ch in vowels:
            count += 1
    return count
