def alternating_caps(text):
    make_upper = True
    out = []
    for ch in text:
        if ch.isalpha():
            if make_upper:
                out.append(ch.swapcase())
            else:
                out.append(ch.lower())
            make_upper = not make_upper
        else:
            out.append(ch)
    return ''.join(out)
