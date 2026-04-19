def alternating_caps(text):
    make_upper = True
    out = []
    for ch in text:
        if ch.isalpha():
            out.append(ch.upper() if make_upper else ch.lower())
        else:
            out.append(ch)
        make_upper = not make_upper
    return ''.join(out)
