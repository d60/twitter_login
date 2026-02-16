from .utils import n_digit_hex, xor_stream


def rotate_string(s, n):
    if not s:
        return s
    shift = n % len(s)
    return s[shift:] + s[:shift]


def encode_two_values(n1, n2):
    val = ((n1 * 2) & 0xFFF) << 4 | (n2 % 32 & 0xFF)
    return f'{val:04x}'


def encode_lists(lists):
    nums = [0, 4, 7, 8, 9]
    result = []
    for num, lst in zip(nums, lists):
        encoded = encode_two_values(num, len(lst))
        result.append(encoded)
        result.extend([str(item) for item in lst])
    return ''.join(result)


def xor_with_rotated_key(data, key, key_length, rotate_n_hex):
    key_part = key[:key_length]
    n = int(rotate_n_hex, 16)
    shift = n % len(key_part)
    rotated_key = key_part[shift:] + key_part[:shift]
    return xor_stream(data, rotated_key)


def func2(value, i, cuid):
    time_token = value[0]
    xor1 = time_token + xor_with_rotated_key(
        encode_lists(i[6])
        + n_digit_hex(len(i[2]) // 2, 4, stop=True)
        + value[1]
        + i[8]
        + 'ff',
        time_token,
        4,
        time_token[3],
    )

    return (
        i[4]
        + i[5]
        + '4176526137396248794a53595351486e52706356747a79786574537646657278'
        + cuid
        + xor_with_rotated_key(xor1, cuid, 8, cuid[9])
    )

# ''.join(n_digit_hex(i, 2) for i in 'AvRa79bHyJSYSQHnRpcVtzyxetSvFerx'.encode())


# (
#     encode_lists(
#         [
#             [
#                 "0301",
#                 "0b00",
#                 "1408ccb08897f1043b09",
#                 "1e50",
#                 "278500032002f0",
#                 "2d18",
#                 "3516",
#                 "3e0f",
#                 "47dc00",
#                 "4f027d5fc9a7",
#                 "570572930208",
#                 "5f0c007f",
#                 "6701708c8ef3e0819be7e362c617a941cfc14d3a1053c993591fb1313179c649bdbbb837ea7b11f39062b6ea7e0ef6f0d529d7890364360d3ffa70c120802afa9aaefee81909f9c8218bfca21087958c8a76d6a3be868a91e4c4ec8a7675ba6ddd7bd796a9733eb96298b9ecc33f53108e1a51",
#                 "6c081729e512bc3d2d76",
#                 "770307",
#                 "8b00",
#                 "9408e5dadae933642762",
#                 "9c5811d2938dc036f55ee2a20fb8f51523784778ffa8c1e27d7a865e6c41e390313b373c3344dabb9d02161b01f8132e1e6b76e91bffebd315cc56c64605bdc0650238515fb178c5bcb490bd1acd43d2459e90f4f2ba1f6c9436",
#                 "a410e50bdf1cf2a5a751248430d66940c225",
#                 "af0800",
#                 "b521",
#                 "c5ac1e",
#                 "cb00",
#                 "d301",
#                 "dd840a",
#                 "e700",
#                 "eb03",
#                 "f75fd82d5132",
#                 "ffa26a",
#             ],
#             [
#                 "0300",
#                 "0c0c3f80e4984edd22015b4b12eb",
#                 "141899f391177850e940df71e17a50a53c42ca684fd9f4417fd9",
#                 "3506",
#                 "57040a",
#                 "6550",
#                 "6f0b0400",
#                 "71",
#                 "87090000",
#                 "8f0f0722",
#                 "91",
#                 "af01000000",
#                 "b4046a610000",
#                 "c7024b0057",
#                 "d1",
#                 "df0408",
#                 "e301",
#                 "ec00",
#                 "f4106d94a2b1dfa646e1e33398a6597af840",
#             ],
#             [
#                 "0304",
#                 "0c080d5d413d72b2e6c1",
#                 "1301",
#                 "1d01",
#                 "250a",
#                 "2c08d3a09da709c0dc6d",
#                 "3701047b7d0000",
#                 "3f2e007fff3fffff",
#                 "4502",
#                 "4d00",
#                 "550d",
#                 "5d8ae6",
#                 "6709000000000000000000002a940000000033f4000000001f4000000003997c00000006590000000005d3cc000000000000000000000000",
#                 "69",
#                 "770400",
#                 "7b00",
#                 "870200000000000000002a879be8",
#                 "8f0800",
#                 "9702b50500029902f0",
#                 "9f00000000",
#                 "a300",
#                 "ad00",
#                 "b7000f000f",
#                 "bf00000001031d",
#                 "c4046a610000",
#                 "cd1a",
#                 "d507",
#                 "dd13",
#                 "e301",
#                 "ed80da",
#                 "f40cf583d52a2ec03fe823cb4f1f",
#             ],
#             [
#                 "0531",
#                 "0b00",
#                 "14085a7f390b6dbcca15",
#                 "1d13",
#                 "2c0ce334e7721d6a3302d6c2a068",
#                 "3700000000028a",
#                 "3f2b000000000000",
#                 "4500",
#                 "54081f209322127bfae1",
#                 "5a",
#                 "62",
#                 "6d00",
#                 "7500",
#                 "7d00",
#                 "870400",
#                 "8c00",
#                 "92",
#                 "9e0a",
#                 "a500",
#                 "ad00",
#                 "b9",
#                 "c424297060a7c53fac184fc0633d20843f5072a244f408af6cde984ea80f446efd314531baed",
#                 "cc045b5d0000",
#                 "d45891c277ceca7cdfac347bd692a9a07e1fc974dc172b12168af598c1ac2de6906bb130a7aeaf8a3ec4b062e5d60b08b6249aa15b1a1676aff74a651a54a7f9a04170229219e66e352e3b13876857bbaf3d7310aa1b6e1ae798",
#                 "e580f4",
#                 "ec08722f521a75fb4130",
#             ],
#             [
#                 "0501",
#                 "0c045b5d0000",
#                 "12",
#                 "1a",
#                 "2408f0fef670c5e06d05",
#                 "2a",
#                 "4c702a4dbe12eeac831a3e06190fd0dc85f3789edd995fe863a6574d179847db77b6298aa69c8b79d492859e2cb71e04ab1f8acae7e890150609ca664216bb8897c5a0f3775c0ec60ce2804fed5b420639752fd103ee35a980512dfe32188bbbcf15cab9a45375c4ab20d950f942a6f3813c",
#                 "6408edfa9a27fe7481c3",
#                 "6c0478383600",
#                 "740436340000",
#                 "7c044e410000",
#                 "8408dc706ecd2a92ef5e",
#                 "8c1025f278e340fa123974b0a9325e3dbeaf",
#                 "9494689a0071e219e2c0cf24dc6fb55b3c9012fb36b026ec0f02c501edbb6e30d5a5b6fc1c404639deb2acb32fc66ae2a9d6618ac642a3306f86b50c97348fc5c838d02e9d054fbd0df47bb3a70f0ae0903daa2864a84d5a00faf1c510d34badf7e029a76b42a7c622408527a85b652293d00f74659f71f1f56d6da0d108a533e08f378459969401c0a38875c587ce92d6e258d19435",
#                 "a40c4c1ea2a87874a250af7d1172",
#                 "ad9a80",
#                 "b524",
#                 "bd01",
#                 "c50c",
#                 "cd06",
#                 "d500",
#                 "dc082cb91e850687234c",
#                 "e505",
#                 "ed02",
#                 "f587ea",
#                 "fc084b274412fdeb4f1c",
#             ],
#         ]
#     )
# )
