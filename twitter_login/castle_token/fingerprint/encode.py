import math

from ..utils import arr_to_2dig_hex_string, n_digit_hex
from ..xxtea_encrypt import xxtea_encrypt


def to_byte_array_manual(int_array):
    result = []
    for num in int_array:
        num = num & 0xFFFFFFFF
        result.append(num & 255)
        result.append((num >> 8) & 255)
        result.append((num >> 16) & 255)
        result.append((num >> 24) & 255)
    return result


def time_index_encrypt(index, input, time):
    time_unsigned = time & 0xFFFFFFFF
    return to_byte_array_manual(
        xxtea_encrypt(input.encode(), [index, time_unsigned, 2107336303, 2241668600, 1517820919, 2554034554, 1164413191])
    )


def encode_xxtea_frame(index, data, time):
    xxtea_encrypted = time_index_encrypt(index, data, time)

    def calc_byte_length(n):
        length = 0
        while n != 0:
            n >>= 8
            length += 1
        return length

    byte_length = calc_byte_length(len(xxtea_encrypted))
    return (
        n_digit_hex(byte_length, 2)
        + n_digit_hex(len(xxtea_encrypted), 2)
        + arr_to_2dig_hex_string(xxtea_encrypted)
    )


def prepare_value(index, case):
    return n_digit_hex((index & 31) << 3 | case & 7, 2)


def encode_field_case3(index, input, _):
    case = 3
    value = prepare_value(index, case)
    return value + n_digit_hex(input, 2)


def encode_field_case4(index, input, time):
    case = 4
    value = prepare_value(index, case)
    arr = time_index_encrypt(index, input, time)
    return value + n_digit_hex(len(arr), 2) + arr_to_2dig_hex_string(arr)


def encode_field_case5(index, input, _):
    case = 5
    value = prepare_value(index, case)

    if (input & 0x7FFF) > 127:
        num = (1 << 15) | (input & 0x7FFF)
        hex = n_digit_hex(num, 4)
    else:
        hex = n_digit_hex(input & 0xFF, 2)

    return value + hex


def encode_field_case6(index, input, _):
    case = 6
    value = prepare_value(index, case)
    return value + n_digit_hex(round(input * 10), 2)


def encode_field_case7(index, input, _):
    case = 7
    value = prepare_value(index, case)
    return value + input


def encode_field_default(index, input, _, case):
    return prepare_value(index, case)


ENCODE_FUNCTIONS = {
    3: encode_field_case3,
    4: encode_field_case4,
    5: encode_field_case5,
    6: encode_field_case6,
    7: encode_field_case7
}


def encode_field(index, case, input, time = None):
    # WK[Cx]
    # arguments = (e, t, r, i)
    if case not in ENCODE_FUNCTIONS:
        return encode_field_default(index, input, time, case)
    encode_function = ENCODE_FUNCTIONS[case]
    return encode_function(index, input, time)


def index_of(arr, value):
    if value in arr:
        return arr.index(value)
    return -1


def encode_optional_index(index, input1, input2, time):
    case = 3
    input = input1
    if input1 == -1:
        case = 4
        input = input2
    return encode_field(index, case, input, time)


def bits_to_hex(bits):
    # WK[iE]
    length_prefix = f'{len(bits) & 255:02x}'
    normalized_bits = list(map(bool, bits))

    body_hex = ''
    chunk_size = 24
    for i in range(0, len(normalized_bits), chunk_size):
        chunk = normalized_bits[i : i + chunk_size]

        val = 0
        for bit in chunk:
            val = (val << 1) | bit
        chunk_len = len(chunk)
        if chunk_len == chunk_size:
            num_bytes = 3
        else:
            num_bytes = math.ceil(chunk_len / 8)
        body_hex += n_digit_hex(val, num_bytes * 2)
    return length_prefix + body_hex


def pack_15_16_bits(value1, value2):
    # WK[aV]
    v1_15bits = value1 & 32767
    v2_16bits = value2 & 65535

    if v1_15bits == v2_16bits:
        return n_digit_hex(v1_15bits | 32768, 4)
    else:
        return n_digit_hex(v1_15bits, 4) + n_digit_hex(v2_16bits, 4)
