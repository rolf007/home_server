def filify(s):
    table = {32: '_',
             47: '_',
             197: 'Aa',
             198: 'Ae',
             216: 'Oe',
             229: 'aa',
             230: 'ae',
             248: 'oe'}

    ret = ""
    for c in s:
        o = ord(c)
        if o in table:
            ret += table[o]
        elif o >= 32 and o <= 126:
            ret += c
    return ret
