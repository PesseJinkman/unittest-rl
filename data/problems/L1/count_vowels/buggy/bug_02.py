def count_vowels(text):
    vowels = "aeiouyAEIOUY"
    count = 0
    for ch in text:
        if ch in vowels:
            count += 1
    return count
