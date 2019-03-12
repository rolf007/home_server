
def multi_dict_to_dict_of_lists(md):
    e = {}
    for kv in md.items():
        if kv[0] not in e:
            e[kv[0]] = []
        e[kv[0]].append(kv[1])
    return e

