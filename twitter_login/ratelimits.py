import time
from dataclasses import dataclass
from urllib.parse import urlparse
from curl_cffi import Headers


@dataclass(frozen=True)
class Ratelimit:
    limit: int
    remaining: int
    reset: int

    def is_reset(self) -> bool:
        return self.reset < time.time()

    def is_limited(self) -> bool:
        return not self.is_reset() and self.remaining <= 0

    def current_remaining(self):
        if self.is_reset():
            return self.limit
        return self.remaining


def normalize_url(url: str):
    if not isinstance(url, str):
        return
    if "://" not in url:
        url = "http://" + url
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return
    hostname = hostname.lower()
    path = parsed.path.strip('/')
    if path:
        return f'{hostname}/{path}'
    return hostname


class RatelimitsManager:
    def __init__(self) -> None:
        self.ratelimits: dict[str, Ratelimit] = {}

    def update(self, url, headers: Headers):
        args = (
            headers.get('x-rate-limit-limit'),
            headers.get('x-rate-limit-remaining'),
            headers.get('x-rate-limit-reset')
        )
        if not all(args):
            return
        try:
            args = [int(v) for v in args]
        except (TypeError, ValueError):
            return
        normalized_url = normalize_url(url)
        if not normalized_url:
            return
        self.ratelimits[normalized_url] = Ratelimit(*args)

    def get(self, url):
        normalized_url = normalize_url(url)
        if not normalized_url:
            return
        return self.ratelimits.get(normalized_url)

    def is_limited(self, url):
        ratelimit = self.get(url)
        if not ratelimit:
            return False
        return ratelimit.is_limited()

    def __repr__(self) -> str:
        return repr(self.ratelimits)
