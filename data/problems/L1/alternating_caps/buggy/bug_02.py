def alternating_caps(text):
    make_upper = False
    out = []
    for ch in text:
        if ch.isalpha():
            out.append(ch.upper() if make_upper else ch.lower())
            make_upper = not make_upper
        else:
            out.append(ch)
    return ''.join(out)
