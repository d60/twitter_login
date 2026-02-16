from itertools import cycle


def n_digit_hex(value, n, stop = False):
    if stop:
        max_value = 16 ** n - 1
        value = min(value, max_value)
    mask = (1 << (4 * n)) - 1
    return f'{value & mask:0{n}x}'


def xor_stream(data, key):
    key_cycle = cycle(key)
    result = ''
    for hex_digit, key_digit in zip(data, key_cycle):
        xor = int(hex_digit, 16) ^ int(key_digit, 16)
        result += format(xor, 'x')
    return result


def arr_to_2dig_hex_string(arr):
    return ''.join(map(lambda x: n_digit_hex(x, 2), arr))
