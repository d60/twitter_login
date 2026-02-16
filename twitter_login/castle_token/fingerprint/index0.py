import mmh3

from ..utils import n_digit_hex
from .encode import (
    bits_to_hex,
    encode_field,
    encode_optional_index,
    encode_xxtea_frame,
    index_of,
    pack_15_16_bits
)


def index0(platform, time=None):
    # window.navigator.platform
    PLATFORMS = [
        'MacIntel',
        'Win32',
        'iPhone',
        'Linux armv8l',
        'iPad',
        'Linux armv81',
        'Linux aarch64',
        'Linux x86_64',
        'Linux armv7l',
    ]
    index = index_of(PLATFORMS, platform)
    return encode_optional_index(0, index, platform, time)


def index1(vendor, time=None):
    # window.navigator.vendor
    VENDORS = ['Google Inc.', 'Apple Computer, Inc.']
    index = index_of(VENDORS, vendor)
    return encode_optional_index(1, index, vendor, time)


def index2(language, time=None):
    """
    window.navigator.language ||
    window.navigator.userLanguage ||
    window.navigator.browserLanguage ||
    window.navigator.systemLanguage
    """
    LANGUAGES = [
        'US-US',
        'ES-ES',
        'FR-FR',
        'BR-BR',
        'GB-GB',
        'DE-DE',
        'RU-RU',
        'us-us',
        'gb-gb',
        'CN-CN',
        'ID-ID',
        'US-US',
        'IT-IT',
        'MX-MX',
        'PL-PL',
    ]
    index = index_of(LANGUAGES, language)
    return encode_optional_index(2, index, language, time)


def index3(device_memory):
    # window.navigator.deviceMemory
    if device_memory > 25.5:
        device_memory = round(device_memory)
        return encode_field(3, 5, round(device_memory))
    else:
        return encode_field(3, 6, device_memory)


def index4(width, avail_width, height, avail_height):
    # pack_15_16_bits(window.screen.width, window.screen.availWidth) +
    # pack_15_16_bits(window.screen.height, window.screen.availHeight)
    encoded = pack_15_16_bits(width, avail_width) + pack_15_16_bits(
        height, avail_height
    )
    return encode_field(4, 7, encoded)


def index5(color_depth=None, pixel_depth=None):
    """
    window.screen.colorDepth ||
    window.screen.pixelDepth
    """
    if not (color_depth or pixel_depth):
        raise ValueError('color_depth or pixel_depth is required')
    return encode_field(5, 5, color_depth or pixel_depth)


def index6(hardware_concurrency):
    # window.navigator.hardwareConcurrency
    return encode_field(6, 5, hardware_concurrency)


def index7(device_pixel_ratio):
    """
    window.devicePixelRatio ||
    window.screen.systemXDPI / window.screen.logicalXDPI
    """
    if device_pixel_ratio > 25.5:
        device_pixel_ratio = round(device_pixel_ratio)
        return encode_field(7, 5, round(device_pixel_ratio))
    else:
        return encode_field(7, 6, device_pixel_ratio)


def index8(timezone_offset, summertime_offset_diff):
    """
    v1: (new Date).getTimezoneOffset()
    v2 = (function () {
        var e = [];
        return e[1] = new Date,
            e[1]['setDate'](1),
            e[1]['setMonth'](0),
            e[2] = e[1]['getTimezoneOffset'](),
            e[1]['setMonth'](6),
            e[0] = e[1]['getTimezoneOffset'](),
            Math.abs(e[2] - e[0])
    })()
    n_dig_hex(v1 // 15, 2) + n_dig_hex(v2 // 15, 2)
    """
    value = n_digit_hex(timezone_offset // 15, 2) + n_digit_hex(
        summertime_offset_diff // 15, 2
    )
    return encode_field(8, 7, value)


def index9(mime_types):
    # ['application/pdf', 'text/pdf']
    # Array.from(navigator.mimeTypes, m => m.type)
    s = "".join(sorted(mime_types))
    mmh3_hashed = mmh3.hash(s)
    value = n_digit_hex(len(mime_types), 2) + n_digit_hex(mmh3_hashed, 8, stop=True)
    return encode_field(9, 7, value)


def index10(plugins):
    """
    Array.from(navigator.plugins, p =>
        p.name + p.description + p.length + p.filename
    )
    """
    s = ''.join(sorted(plugins))
    mmh3_hashed = mmh3.hash(s)
    value = n_digit_hex(len(plugins), 2) + n_digit_hex(mmh3_hashed, 8, stop=True)
    return encode_field(10, 7, value)


def index11(bits):
    """
    [
        false,
        window.document.documentMode,
        'opr' in window && !!window.opr,
        window.navigator.oscpu,
        window.navigator.webdriver,
        'chrome' in window && !!window.chrome,
        window.navigator.serviceWorker,
        window.navigator.permissions,
        window.navigator.storage,
        window.navigator.bluetooth,
        window.navigator.credentials,
        window.navigator.cookieEnabled
    ].map(e=>Boolean(e))
    """
    hex = bits_to_hex(bits)
    return encode_field(11, 7, hex)


def index12(user_agent, time):
    # window.navigator.userAgent
    # xxtea_encrypted = time_index_encrypt(12, user_agent, time)

    # def calc_byte_length(n):
    #     length = 0
    #     while n != 0:
    #         n >>= 8
    #         length += 1
    #     return length

    # byte_length = calc_byte_length(len(xxtea_encrypted))
    # hex = (
    #     n_digit_hex(byte_length, 2)
    #     + n_digit_hex(len(xxtea_encrypted), 2)
    #     + arr_to_2dig_hex_string(xxtea_encrypted)
    # )
    hex = encode_xxtea_frame(12, user_agent, time)
    return encode_field(12, 7, hex)


def index13(canvas_fingerprinting_hash, time):
    """
    dataURL = (function () {
        let canvas = window.document.createElement('canvas');
        let context = canvas.getContext('2d');
        return (function (e, t) {
            var r = [];
            return e.width = 500,
                e.height = 100,
                r[0] = 'Yxskaftbud, ge vår WC-zonmö IQ-hjälp. ' + '😄',
                t.textBaseline = 'alphabetic',
                t.fillStyle = '#f60',
                t.fillRect(125, 1, 62, 20),
                t.fillStyle = '#069',
                t.font = '13pt bogus-font-xxx',
                t.fillText(r[0], 2, 20),
                t.fillStyle = 'rgba(102, 204, 0, 0.6123456789)',
                t.font = '16pt Arial',
                t.fillText(r[0], 4, 22),
                e.toDataURL()
        })(canvas, context)
    })()
    HEX(MMH3(dataURL))
    """
    return encode_field(13, 4, canvas_fingerprinting_hash, time)


def index14(enumerate_devices_bits):
    """
    js/014.js

    3 boolean bits [
        audiooutput available,
        audioinput available,
        videoinput available
    ]

    let devices = await navigator.mediaDevices.enumerateDevices();
    [
        devices.some(d => d.kind === 'audiooutput'),
        devices.some(d => d.kind === 'audioinput'),
        devices.some(d => d.kind === 'videoinput'),
    ];
    """
    hex = bits_to_hex(enumerate_devices_bits)
    return encode_field(14, 7, hex)


# 15, 16 = missing


def index17(product_sub, time=None):
    # window.navigator.productSub
    # '20030107' or '20100101'
    PRODUCT_SUBS = ['20030107', '20100101']
    index = index_of(PRODUCT_SUBS, product_sub)
    return encode_optional_index(17, index, product_sub, time)


def index18(canvas_fingerprinting_hash, time):
    """
    (function () {
        let canvas = window.document.createElement('canvas');
        let context = canvas.getContext('2d');
        return (function (e, t) {
            var r = [];
            e.width = 400;
            e.height = 200;
            t.globalCompositeOperation = 'multiply';
            let data = [
                ["#f0f", 50, 50],
                ["#0ff", 100, 50],
                ["#f70", 75, 100]
            ];
            for (var i = 0, u = data; i < u.length; i++) {
                r[0] = u[i];
                r[1] = r[0][0];
                r[0][1];
                r[0][2];
                t.fillStyle = r[1];
                t.beginPath();
                t.arc(75, 75, 75, 0, 6.283185307179586, true);
                t.closePath();
                t.fill();
            }
            return t.fillStyle = '#70f',
                t.arc(75, 75, 75, 0, 6.283185307179586, true),
                t.arc(75, 75, 75, 0, 6.283185307179586, true),
                t.fill('evenodd'),
                e.toDataURL();
        })(canvas, context)
    })()
        HEX(MMH3(dataURL))
    """
    return encode_field(18, 4, canvas_fingerprinting_hash, time)


def index19(WebGL_renderer, time):
    # WK[tR]
    # js/019.js
    # 'ANGLE (Intel, Intel(R) Arc(TM) Graphics (0x00007D55) Direct3D11 vs_5_0 ps_5_0, D3D11)'
    return encode_field(19, 4, WebGL_renderer, time)


def index20(epoch_plus_two_months, time):
    # WK[$d]
    """
    (function () {
        let date = new Date;
        date.setTime(0);
        date.setMonth(date.getMonth() + 2);
        return date.toLocaleString();
    })()
    """
    return encode_field(20, 4, epoch_plus_two_months, time)


def index21(detect_automation_bits):
    # js/021.js
    # [false * 8] -> 0800
    hex = bits_to_hex(detect_automation_bits)
    return encode_field(21, 7, hex)


def index22(eval_length):
    # (window.eval ? window.eval.toString().length : 0)
    #   -> 33: Chrome, Opera, Edge
    #   -> 37: Safari, Firefox
    #   -> 39: IE
    return encode_field(22, 5, eval_length)


#  23 = missing


def index24(maximum_call_stack_size):
    # WK[ux]() 11171
    return encode_field(24, 5, maximum_call_stack_size)


def index25(maximum_call_stack_size_exceeded_message, time=None):
    # WK[ux]()
    # 'Maximum call stack size exceeded'
    MESSAGES = [
        'Maximum call stack size exceeded',
        'Maximum call stack size exceeded.',
        'too much recursion',
    ]
    index = index_of(MESSAGES, maximum_call_stack_size_exceeded_message)
    return encode_optional_index(
        25, index, maximum_call_stack_size_exceeded_message, time
    )


def index26(maximum_call_stack_size_exceeded_name, time=None):
    # WK[ux]()
    # 'RangeError'
    NAMES = ['InternalError', 'RangeError', 'Error']
    index = index_of(NAMES, maximum_call_stack_size_exceeded_name)
    return encode_optional_index(26, index, maximum_call_stack_size_exceeded_name, time)


def index27(maximum_call_stack_size_exceeded_stack_length):
    # WK[ux]() 1034
    return encode_field(27, 5, maximum_call_stack_size_exceeded_stack_length)


def index28(touch_signature_hex):
    # js/028.js
    return encode_field(28, 7, touch_signature_hex)


def index29(read_property_of_undefined_message, time=None):
    """
    (function () {
        try {
            return [][0]['b'],
                ''
        } catch (e) {
            return e.message
        }
    })
    """
    MESSAGES = [
        "Cannot read property 'b' of undefined",
        "(void 0) is undefined",
        "undefined is not an object (evaluating '(void 0).b')",
        "Cannot read properties of undefined (reading 'b')",
    ]
    index = index_of(MESSAGES, read_property_of_undefined_message)
    return encode_optional_index(29, index, read_property_of_undefined_message, time)


def index30(navigator_properties):
    # js/030.js
    s = ''.join(sorted(navigator_properties))
    mmh3_hashed = mmh3.hash(s)
    value = n_digit_hex(len(navigator_properties), 2) + n_digit_hex(
        mmh3_hashed, 8, stop=True
    )
    return encode_field(30, 7, value)


def index31(can_play_type_values):
    # js/031.js
    result = int(''.join(format(v & 3, '02b') for v in can_play_type_values), 2)
    hex = n_digit_hex(result, 4, True)
    return encode_field(31, 7, hex)
