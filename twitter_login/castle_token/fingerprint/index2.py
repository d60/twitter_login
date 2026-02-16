from .encode import (
    bits_to_hex,
    encode_field,
    encode_optional_index,
    encode_xxtea_frame,
    index_of,
    pack_15_16_bits
)
from ..utils import n_digit_hex


def base256_4dig(n):
    MAX = 256**4 - 1
    if n < 0 or n > MAX:
        return [0, 0, 0, 0]
    d1 = (n >> 24) & 0xFF
    d2 = (n >> 16) & 0xFF
    d3 = (n >> 8) & 0xFF
    d4 = n & 0xFF
    return [d4, d3, d2, d1]


def arr_to_12dig_hex_seq(arr):
    def to_12dig_hex(n):
        return '0000' + n_digit_hex(max(0, round(n * 1000)), 8, stop=True)

    length_hex = n_digit_hex(len(arr), 2)
    return length_hex + ''.join(map(to_12dig_hex, arr))


def index0(platform, time=None):
    # js/127.js
    # getHighEntropyValues platform
    PLATFORMS = ["Android", "iOS", "macOS", "Linux", "Windows", "Unknown"]
    index = index_of(PLATFORMS, platform)
    return encode_optional_index(0, index, platform, time)


def index1(platform_version, time):
    # js/127.js
    # getHighEntropyValues platformVersion
    return encode_field(1, 4, platform_version, time)


def index2(browser_brand, time=None):
    # js/202.js
    BRANDS = ["Chromium", "Google Chrome", "Opera", "Brave", "Microsoft Edge"]
    index = index_of(BRANDS, browser_brand)
    return encode_optional_index(2, index, browser_brand, time)


def index3(time_diff):
    # js/203.js
    return encode_field(3, 5, time_diff)


def index4(utc_minutes):
    # (new Date(time).getUTCMinutes()
    # time must be init time
    return encode_field(4, 5, utc_minutes)


def index5(hostname, time):
    # window.location.hostname
    return encode_field(5, 4, hostname, time)


def index6(object_json, time):
    # empty object {} now
    hex = encode_xxtea_frame(6, object_json, time)
    return encode_field(6, 7, hex)


def index7(fields):
    # TODO
    # 46 fields
    fields.reverse()
    hex = bits_to_hex(fields)
    return encode_field(7, 7, hex)


def index8(available_linux_font_count):
    # js/208-210.js
    return encode_field(8, 5, available_linux_font_count)


def index9(available_mac_font_count):
    # js/208-210.js
    return encode_field(9, 5, available_mac_font_count)


def index10(available_windows_font_count):
    # js/208-210.js
    return encode_field(10, 5, available_windows_font_count)


def index11(canvas_fingerprinting_length):
    # js/211.js
    return encode_field(11, 5, canvas_fingerprinting_length)


def index12(get_navigation_timing_durations):
    # js/212.js
    hex = arr_to_12dig_hex_seq(get_navigation_timing_durations)
    return encode_field(12, 7, hex)


def index13(iframe_navigator_accessible):
    # js/213.js
    case = 2 if iframe_navigator_accessible else 1
    return encode_field(13, case, "")


def index14(canvas_integrity_flags):
    # js/214.js
    hex = bits_to_hex(canvas_integrity_flags)
    return encode_field(14, 7, hex)


def index15(canvas_error_message, time=None):
    # js/214.js
    messages = [
        "Illegal invocation",
        "Can only call CanvasRenderingContext2D.getImageData on instances of CanvasRenderingContext2D",
        "'getImageData' called on an object that does not implement interface CanvasRenderingContext2D.",
    ]
    index = index_of(messages, canvas_error_message)
    return encode_optional_index(15, index, canvas_error_message, time)


def index16(memory_info):
    """
    [
        window.performance.memory.jsHeapSizeLimit,
        window.performance.memory.totalJSHeapSize
    ]
    """
    hex = arr_to_12dig_hex_seq(memory_info)
    return encode_field(16, 7, hex)


def index17(screen_integrity_flags):
    """
    js/217.js
    [
        isScreenExtended,
        isAvailSizeLarger,
        isDocSizeLarger,
        isInnerSizeLarger,
        isOuterSizeLarger,
        isCssDeviceSizeConsistent,
        isDpiInconsistent,
        isFullscreen
    ]
    """
    hex = bits_to_hex(screen_integrity_flags)
    return encode_field(17, 7, hex)


def index18(inner_width, outer_width, inner_height, outer_height):
    # window.innerWidth, window.outerWidth, window.innerHeight, window.outerHeight
    hex = pack_15_16_bits(inner_width, outer_width) + pack_15_16_bits(inner_height, outer_height)
    return encode_field(18, 7, hex)


def index19(avail_left, avail_top):
    # window.screen.availLeft, window.screen.availTop
    hex = n_digit_hex(avail_left, 4) + n_digit_hex(avail_top, 4)
    return encode_field(19, 7, hex)


def index20(screen_orientation_type, time = None):
    # window.screen.orientation.type
    SCREEN_ORIENTATION_TYPES = ['landscape-primary', 'portrait-primary', 'landscape-secondary', 'portrait-secondary']
    index = index_of(SCREEN_ORIENTATION_TYPES, screen_orientation_type)
    return encode_optional_index(20, index, screen_orientation_type, time)


def index21(screen_orientation_angle):
    # window.screen.orientation.angle
    return encode_field(21, 5, screen_orientation_angle)


def index22(scroll_bar_width, scroll_bar_height):
    hex = n_digit_hex(scroll_bar_width, 4) + n_digit_hex(scroll_bar_height, 4)
    return encode_field(22, 7, hex)


def index23(canvas_read_performance_ratio):
    # js/223.js
    x1000 = round(canvas_read_performance_ratio * 1000)
    hex = '0000' + n_digit_hex(x1000, 8, stop=True)
    return encode_field(23, 7, hex)


def index24(default_voice_lang, time):
    # js/224-228.js
    return encode_field(24, 4, default_voice_lang, time)


def index25(voices_length):
    # js/224-228.js
    return encode_field(25, 5, voices_length)


def index26(local_voices_length):
    # js/224-228.js
    return encode_field(26, 5, local_voices_length)


def index27(google_voices_length):
    # js/224-228.js
    return encode_field(27, 5, google_voices_length)


def index28(voice_os, time = None):
    # js/224-228.js
    OS_LIST = ['macOS', 'Windows', 'ChromeOS', 'Android', 'Other']
    index = index_of(OS_LIST, voice_os)
    return encode_optional_index(28, index, voice_os, time)


def index29(render_latency):
    # js/229.js
    return encode_field(29, 5, render_latency)


def index30(keyboard_hash, time):
    # js/230.js
    return encode_field(30, 4, keyboard_hash, time)
