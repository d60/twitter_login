def optional_chaining(dict_, *chain, default = None):
    """
    Implementation of optional chaining.
    a?.b?.c =  optional_chaining(a, 'b', 'c')
    """
    cur = dict_
    for key in chain:
        if not isinstance(cur, dict):
            return default
        if key not in cur:
            return default
        cur = cur[key]
    return cur
