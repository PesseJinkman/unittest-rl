def count_vowels(text):
    vowels = 'aeiou'
    count = 0
    for ch in text:
        if ch in vowels:
            count += 1
    return count
