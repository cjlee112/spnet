import re

def convert_tex_dollars(t):
    'do our best to convert $inlinemath$ to \(inlinemath\)'
    i = 0
    l = []
    n = len(t)
    while True:
        j = t.find('$', i)
        if j < 0:
            break
        elif j > 0 and t[j - 1] == '\\': # ignore escaped $
            continue
        if len(l) % 2: # looking for close
            if not t[j - 1].isspace(): # must be preceded by non-ws character
                l.append(j)
        elif j + 1 < n and not t[j + 1].isspace() and t[j + 1] not in '.,:;':
            l.append(j) # open must be followed by non-ws
        i = j + 1
    if len(l) % 2:
        return t + ' (TeX $ CONVERSION FAILED: unbalanced $)'
    out = []
    last = 0
    for i in range(0, len(l), 2):
        start, stop = l[i:i + 2]
        out.append(t[last:start])
        out.append('\\(' + t[start + 1:stop] + '\\)')
        last = stop + 1
    out.append(t[last:])
    return ''.join(out)
