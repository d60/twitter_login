import base64
import re

from .utils import n_digit_hex, xor_stream


def hex_to_bin(hex_str):
    return bytes(int(hex_str[i : i + 2], 16) for i in range(0, len(hex_str), 2))


def func4(value, i):
    n = hex_to_bin(i[3] + xor_stream(value + n_digit_hex(len(value), 2), i[3]))
    b64 = base64.b64encode(n).decode()
    return re.sub(r'=+$', '', b64.replace('+', '-').replace('/', '_'))
