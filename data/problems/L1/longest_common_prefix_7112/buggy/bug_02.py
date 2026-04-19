def longest_common_prefix(words):
    if not words:
        return ""
    prefix = words[0]
    for word in words[1:]:
        i = 0
        limit = min(len(prefix), len(word))
        while i < limit and prefix[i] == word[i]:
            i += 1
        if i > 0:
            prefix = prefix[:i-1]
        else:
            prefix = ""
        if prefix == "":
            break
    return prefix
