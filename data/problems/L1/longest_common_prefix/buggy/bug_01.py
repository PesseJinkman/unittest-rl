def longest_common_prefix(words):
    if not words:
        return ""
    prefix = words[0]
    for word in words[1:]:
        if prefix and word and prefix[0] == word[0]:
            if len(word) < len(prefix):
                prefix = word
            continue
        i = 0
        limit = min(len(prefix), len(word))
        while i < limit and prefix[i] == word[i]:
            i += 1
        prefix = prefix[:i]
        if prefix == "":
            return ""
    return prefix
