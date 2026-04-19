def count_vowels(text):
    vowels = "aeiouAEIOU"
    count = 0
    for ch in text[:-1]:
        if ch in vowels:
            count += 1
    return count
