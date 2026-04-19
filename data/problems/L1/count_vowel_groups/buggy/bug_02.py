def count_vowel_groups(text):
    vowels = 'aeiou'
    count = 0
    in_group = False
    for ch in text:
        if ch in vowels:
            if not in_group:
                count += 1
                in_group = True
        else:
            in_group = False
    return count
