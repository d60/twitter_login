from .utils import n_digit_hex


def encode_to_4dig_hex(n):
    value = n << 11 | 258
    return n_digit_hex(value, 4, stop=True)
