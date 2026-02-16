from .utils import arr_to_2dig_hex_string, n_digit_hex
from .xxtea_encrypt import xxtea_encrypt


def hex_to_int_arr(hex_str):
    # 16進数を2桁ずつ区切って整数のリストに
    arr = []
    for i in range(0, len(hex_str), 2):
        arr.append(int(hex_str[i:i+2], 16))
    return arr


def process1(data):
    key = [1164413191, 3891440048, 218959117, 2746598870]

    enc = xxtea_encrypt(data, key)

    bytes_list = []
    for v in enc:
        v &= 0xFFFFFFFF
        bytes_list.extend([
            v & 0xFF,
            (v >> 8) & 0xFF,
            (v >> 16) & 0xFF,
            (v >> 24) & 0xFF,
        ])

    return len(data), bytes_list


def process2(data):
    return (
        '0d'
        + n_digit_hex(len(data[1]) - data[0], 2)
        + arr_to_2dig_hex_string(data[1])
    )


def func3(data):
    return process2(process1(hex_to_int_arr(data)))
