def count_vowels(text):
    vowels = 'aeiouAEIOU'
    seen = set()
    for ch in text:
        if ch in vowels:
            seen.add(ch.lower())
    return len(seen)
