class Unset:
    def __repr__(self) -> str:
        return '<UNSET>'

# this value will be removed from the params dict
UNSET = Unset()


def remove_unset(dict_):
    return {k: v for k, v in dict_.items() if v is not UNSET}
