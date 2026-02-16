from .utils import arr_to_2dig_hex_string, n_digit_hex, xor_stream


def encode_time_hex(t):
    time_diff = int(t / 1000 - 1535000000)
    arr = [time_diff >> 24, time_diff >> 16, time_diff >> 8, time_diff]
    return arr_to_2dig_hex_string(arr)


def make_time_token(t, random_value):
    random_hex = format(random_value, 'x')
    time_hex = encode_time_hex(t)
    mod_1000_hex = n_digit_hex(t % 1000, 4)
    return (
        xor_stream(time_hex[1:], random_hex)
        + random_hex
        + xor_stream(mod_1000_hex, random_hex)[1:]
        + random_hex
    )


# print(make_time_token(1770215340934, 1))
