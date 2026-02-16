import math


def xxtea_encrypt(e, t):
    def to_uint32_array(data):
        res = []
        for r in range(math.ceil(len(data) / 4)):
            val = (
                (data[r * 4] if r * 4 < len(data) else 0)
                | ((data[r * 4 + 1] if r * 4 + 1 < len(data) else 0) << 8)
                | ((data[r * 4 + 2] if r * 4 + 2 < len(data) else 0) << 16)
                | ((data[r * 4 + 3] if r * 4 + 3 < len(data) else 0) << 24)
            )
            res.append(val & 0xFFFFFFFF)
        return res

    v = to_uint32_array(e)
    n = len(v) - 1

    if n < 1:
        return v

    sum_val = 0
    z = v[n]
    y = v[0]
    DELTA = 2654435769
    mask = 0xFFFFFFFF

    rounds = 6 + 52 // (n + 1)
    for _ in range(rounds):
        sum_val = (sum_val + DELTA) & mask
        e_val = (sum_val >> 2) & 3
        p = 0
        while p < n:
            y = v[p + 1]
            mx = ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4)) ^ (
                (sum_val ^ y) + (t[p & 3 ^ e_val] ^ z)
            )
            v[p] = (v[p] + mx) & mask
            z = v[p]
            p += 1
        y = v[0]
        mx = ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4)) ^ (
            (sum_val ^ y) + (t[p & 3 ^ e_val] ^ z)
        )
        v[n] = (v[n] + mx) & mask
        z = v[n]

    return v
