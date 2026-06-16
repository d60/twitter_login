import base64
import struct
from io import BytesIO

CHUNK_SIZE_BYTES = 4
JETFUEL_VERSION = 'JP-5'


class Jetfuel5ChunkReader:
    """
    Decodes Jetfuel5 response.
    """
    def __init__(self, data: str | bytes):
        if isinstance(data, str):
            data = base64.b64decode(data)
        self.buffer = BytesIO(data)
        self.size = self.buffer.getbuffer().nbytes

    def remaining_size(self):
        return self.size - self.buffer.tell()

    def read_chunk_size(self) -> int:
        return int.from_bytes(
            self.buffer.read(CHUNK_SIZE_BYTES), 'little'
        )

    def read_chunks(self):
        while True:
            if self.remaining_size() <= CHUNK_SIZE_BYTES:
                break
            size = self.read_chunk_size()
            if self.remaining_size() < size:
                break

            data = self.buffer.read(size)
            if not data:
                break

            chunk = Chunk(data)
            yield chunk


class Chunk:
    def __init__(self, data: bytes):
        self.buffer = BytesIO(data)
        self.parse_type = self.u8()

    def u8(self):
        return int.from_bytes(self.buffer.read(1), 'little', signed=False)
    def i16(self):
        return int.from_bytes(self.buffer.read(2), 'little', signed=True)
    def i32(self):
        return int.from_bytes(self.buffer.read(4), 'little', signed=True)
    def i64(self):
        return int.from_bytes(self.buffer.read(8), 'little', signed=True)
    def f64(self):
        val = self.buffer.read(8)
        return struct.unpack('<d', val)[0] if len(val) == 8 else 0.0
    def bool(self):
        return bool(self.u8())
    def uint(self):
        return self.read_varint()
    def str(self):
        l = self.uint()
        return self.buffer.read(l).decode('utf-8', errors='ignore')
    def read_varint(self):
        t = 0
        r = 0
        while True:
            byte_data = self.buffer.read(1)
            if not byte_data:
                return t
            e = byte_data[0]
            if r < 28:
                t += (127 & e) << r
            else:
                t += (127 & e) * (2 ** r)
            if not (128 & e):
                break
            r += 7
        return t

    def parse_elements(self):
        map_results = lambda dct: lambda: {k: v() for k, v in dct.items()}
        u8_ = lambda: self.u8()
        uint_ = lambda: self.uint()
        combine_repeat_ = lambda key_f, val_f: lambda: {key_f(): val_f() for _ in range(self.uint())}
        repeat_ = lambda f: lambda: [f() for _ in range(self.uint())]
        apply_if_true_ = lambda f: lambda: f() if self.bool() else None
        i16_ = lambda: self.i16()
        i32_ = lambda: self.i32()
        i64_ = lambda: self.i64()
        f64_ = lambda: self.f64()
        bool_ = lambda: self.bool()
        const_and_result = lambda const_val, f: lambda: [const_val, f()]
        str_ = lambda: self.str()

        def function_table(e):
            r = {}
            def o():
                tag = self.u8()
                return r[tag]()
            if callable(e):
                r.update(e(o))
            else:
                r.update(e)
            return o

        combine_2_ = lambda f1, f2: lambda: [f1(), f2()]
        combine_3_ = lambda f1, f2, f3: lambda: [f1(), f2(), f3()]
        combine_4_ = lambda f1, f2, f3, f4: lambda: [f1(), f2(), f3(), f4()]
        combine_5_ = lambda f1, f2, f3, f4, f5: lambda: [f1(), f2(), f3(), f4(), f5()]
        do_nothing_ = lambda e: lambda: e

        ELEMENTS_PARSERS = map_results({
            'type': i16_,
            'props': combine_repeat_(i16_, uint_),
            'children': repeat_(uint_),
            'id': apply_if_true_(i64_),
            'extend': apply_if_true_(uint_)
        })

        b = function_table({
            0: const_and_result(0, map_results({'id': i64_})),
            4: const_and_result(4, map_results({'id': i64_, 'root': uint_})),
            1: const_and_result(1, map_results({'key': i16_, 'root': uint_})),
            2: const_and_result(2, map_results({'key': str_, 'root': uint_})),
            3: const_and_result(3, map_results({'key': str_, 'root': uint_})),
            5: const_and_result(5, map_results({'root': uint_})),
            6: const_and_result(6, map_results({'root': uint_})),
            7: const_and_result(7, map_results({'key': str_, 'root': uint_})),
            8: const_and_result(8, map_results({'key': str_, 'root': uint_})),
            9: const_and_result(9, map_results({'root': uint_})),
            10: const_and_result(10, map_results({'root': uint_})),
            11: const_and_result(11, map_results({'root': uint_}))
        })

        j = map_results({
            'ref': b,
            'prop_ref': uint_,
            'is_default': bool_
        })
        y = map_results({
            'ref': b
        })
        _dollar = function_table({
            0: const_and_result(0, b),
            1: const_and_result(1, combine_2_(b, uint_)),
            2: const_and_result(2, combine_2_(b, i16_)),
            3: const_and_result(3, combine_2_(b, str_)),
            4: const_and_result(4, combine_3_(b, uint_, apply_if_true_(i16_))),
            5: const_and_result(5, combine_2_(b, uint_)),
            6: const_and_result(6, combine_2_(b, apply_if_true_(combine_2_(uint_, uint_)))),
            7: const_and_result(7, combine_2_(b, uint_)),
            8: const_and_result(8, combine_2_(b, uint_))
        })

        M = function_table({
            0: const_and_result(0, map_results({'url': uint_, 'preview': apply_if_true_(uint_), 'replace': bool_})),
            9: const_and_result(9, map_results({'url': uint_, 'preview': apply_if_true_(uint_), 'replace': bool_})),
            1: const_and_result(1, map_results({'url': uint_, 'body': apply_if_true_(uint_), 'preview': apply_if_true_(uint_), 'replace': bool_})),
            2: do_nothing_([2]),
            3: do_nothing_([3]),
            4: do_nothing_([4]),
            5: do_nothing_([5]),
            6: do_nothing_([6]),
            7: const_and_result(7, map_results({'id': uint_})),
            8: const_and_result(8, map_results({'url': uint_}))
        })
        k = function_table(lambda e: {
            0: const_and_result(0, _dollar),
            1: const_and_result(1, map_results({'ref': uint_, 'action': e, 'cancel': apply_if_true_(e)})),
            2: const_and_result(2, repeat_(e)),
            3: const_and_result(3, map_results({'url': uint_, 'body': uint_, 'complete': apply_if_true_(e), 'error': apply_if_true_(e), 'optimistic': apply_if_true_(e)})),
            4: const_and_result(4, map_results({'action': e, 'intensity': i16_})),
            5: const_and_result(5, map_results({'ref': uint_, 'type': u8_})),
            6: const_and_result(6, M),
            7: const_and_result(7, map_results({'type': u8_, 'id': apply_if_true_(i64_)})),
            8: const_and_result(8, str_),
            9: const_and_result(9, map_results({'urls': repeat_(str_), 'priority': u8_})),
            10: const_and_result(10, map_results({'action': str_, 'ref': uint_})),
            11: const_and_result(11, map_results({'type': u8_, 'ref': uint_})),
            12: const_and_result(12, map_results({'action': e, 'delaySeconds': i16_})),
            13: const_and_result(13, map_results({'data': str_, 'secret': str_, 'knownDeviceToken': str_})),
            14: const_and_result(14, map_results({'text': str_, 'dismissText': apply_if_true_(str_)})),
            15: const_and_result(15, map_results({'ref': uint_, 'to': uint_})),
            16: const_and_result(16, map_results({'ref': uint_, 'fields': repeat_(str_)})),
            17: const_and_result(17, map_results({'ref': uint_, 'using': uint_})),
            18: const_and_result(18, map_results({'ref': uint_, 'field': str_})),
            19: const_and_result(19, map_results({'ref': uint_, 'type': u8_, 'allowsRotation': bool_})),
            20: const_and_result(20, map_results({'ref': uint_, 'overlay': uint_, 'mode': str_})),
            21: const_and_result(21, map_results({'ref': uint_, 'duration': i16_, 'animation': bool_}))
        })
        z = function_table(lambda e: {
            0: const_and_result(0, map_results({'ref': b})),
            1: const_and_result(1, map_results({'ref': b, 'value': uint_})),
            2: const_and_result(2, map_results({'ref': b, 'value': uint_})),
            3: const_and_result(3, map_results({'ref': b, 'value': repeat_(uint_)})),
            4: const_and_result(4, map_results({'ref': b, 'value': repeat_(uint_)})),
            5: const_and_result(5, map_results({'ref': b, 'value': uint_})),
            6: const_and_result(6, map_results({'ref': b, 'value': uint_})),
            7: const_and_result(7, map_results({'ref': b, 'value': uint_})),
            8: const_and_result(8, map_results({'ref': b, 'value': uint_})),
            9: const_and_result(9, map_results({'ref': b, 'value': str_})),
            10: const_and_result(10, map_results({'ref': b, 'value': str_})),
            11: const_and_result(11, map_results({'ref': b, 'value': str_})),
            12: const_and_result(12, combine_2_(e, e)),
            13: const_and_result(13, combine_2_(e, e)),
            14: const_and_result(14, e),
            15: const_and_result(15, map_results({'ref': b}))
        })
        L = repeat_(repeat_(i32_))
        bar = repeat_(combine_3_(u8_, str_, apply_if_true_(str_)))
        S = combine_5_(str_, combine_repeat_(str_, str_), combine_repeat_(str_, str_), str_, u8_)

        PROPS_PARSERS = function_table({
            0: const_and_result(0, str_),
            1: const_and_result(1, i32_),
            3: const_and_result(3, L),
            4: const_and_result(4, i64_),
            5: const_and_result(5, f64_),
            6: const_and_result(6, bool_),
            7: const_and_result(7, uint_),
            8: const_and_result(8, repeat_(uint_)),
            10: const_and_result(10, uint_),
            11: const_and_result(11, str_),
            12: const_and_result(12, bar),
            13: const_and_result(13, do_nothing_(None)),
            14: const_and_result(14, i64_),
            15: const_and_result(15, uint_),
            16: const_and_result(16, combine_repeat_(i16_, uint_)),
            17: const_and_result(17, combine_repeat_(str_, str_)),
            18: const_and_result(18, j),
            19: const_and_result(19, k),
            21: const_and_result(21, repeat_(uint_)),
            22: const_and_result(22, z),
            24: const_and_result(24, repeat_(uint_)),
            25: const_and_result(25, repeat_(combine_2_(L, z))),
            26: const_and_result(26, repeat_(str_)),
            27: const_and_result(27, repeat_(i32_)),
            28: const_and_result(28, repeat_(f64_)),
            29: const_and_result(29, repeat_(bool_)),
            30: const_and_result(30, S),
            31: const_and_result(31, y)
        })

        H = map_results({
            'els': repeat_(ELEMENTS_PARSERS),
            'props': repeat_(PROPS_PARSERS)
        })

        V = map_results({
            'ref': uint_,
            't': apply_if_true_(i32_)
        })
        if self.parse_type == 0:
            return H()
        elif self.parse_type == 1:
            return V()
        elif self.parse_type == 2:
            return k()
        else:
            raise ValueError(f'Unknown parse type: {self.parse_type}')
