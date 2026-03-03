from enum import Enum
from typing import Sequence, Type, TypeVar


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


T = TypeVar('T', bound=Enum)


def sort_enum_values(values: Sequence[T], enum_class: Type[T]) -> list[T]:
    """
    Sorts enum values by definition order.
    Note that it always returns a list.
    """
    class_values = enum_class.__members__.values()
    for v in values:
        if v not in class_values:
            raise ValueError(f'Unknown enum member for {enum_class.__name__}: {v}')

    value_index = {v: i for i, v in enumerate(class_values)}
    return sorted(values, key=value_index.get)
