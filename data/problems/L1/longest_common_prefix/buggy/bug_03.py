def longest_common_prefix(words):
    if not words:
        return ""
    if len(words) == 1:
        return words[0][:-1]
    prefix = words[0]
    for word in words[1:]:
        i = 0
        limit = min(len(prefix), len(word))
        while i < limit and prefix[i] == word[i]:
            i += 1
        prefix = prefix[:i]
        if prefix == "":
            return ""
    return prefix
