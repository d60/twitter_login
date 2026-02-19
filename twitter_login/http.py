import json
from urllib.parse import urlparse

import curl_cffi
from curl_cffi import Headers, Response

from .constants import AUTHORIZATION, COOKIES_DOMAIN, DEFAULT_HEADERS
from .ratelimits import Ratelimit
from .transaction_id import ClientTransaction


class HTTPError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f'{status_code}: {message}')


class HTTPClient(curl_cffi.AsyncSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ratelimits = {}
        self.client_transaction: ClientTransaction | None = None

    async def request(
        self,
        method: str,
        url: str,
        *args,
        use_transaction_id: bool = True,
        **kwargs,
    ) -> Response:
        if use_transaction_id and self.client_transaction:
            transaction_id = self.client_transaction.generate_transaction_id(method, urlparse(url).path)
            headers = kwargs.get('headers') or {}
            headers['x-client-transaction-id'] = transaction_id
            kwargs['headers'] = headers

        response: Response = await super().request(method, url, *args, **kwargs)
        status_code = response.status_code
        if 400 <= status_code < 600:
            MESSAGE_MEX_LENGTH = 2000
            try:
                message = response.text[:MESSAGE_MEX_LENGTH]
            except:
                message = ''
            raise HTTPError(status_code, message)

        self.update_ratelimit(url, response.headers)
        return response

    def update_ratelimit(self, endpoint: str, response_headers: Headers):
        args = (
            response_headers.get('x-rate-limit-limit'),
            response_headers.get('x-rate-limit-remaining'),
            response_headers.get('x-rate-limit-reset')
        )
        if not all(args):
            return
        try:
            args = [int(v) for v in args]
        except (TypeError, ValueError):
            return
        self.ratelimits[endpoint] = Ratelimit(*args)

    def build_headers(self, *, authorization = True, csrf_token = True, extra_headers = None, json = False):
        headers = DEFAULT_HEADERS.copy()
        if authorization:
            headers['authorization'] = AUTHORIZATION
        if csrf_token:
            csrf_token = self.csrf_token
            if csrf_token is not None:
                headers['x-csrf-token'] = csrf_token
        if extra_headers:
            headers |= extra_headers
        if json:
            headers['Content-Type'] = 'application/json'
        return headers

    @property
    def csrf_token(self):
        return self.cookies.get('ct0', domain=COOKIES_DOMAIN)

    @property
    def guest_token(self):
        return self.cookies.get('gt', domain=COOKIES_DOMAIN)

    def save_cookies(self, path):
        cookies = self.cookies.get_dict(COOKIES_DOMAIN)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f)

    def load_cookies(self, path):
        with open(path, encoding='utf-8') as f:
            cookies = json.load(f)
        if not isinstance(cookies, dict):
            raise ValueError('Cookies format error')
        for k, v in cookies.items():
            self.cookies.set(k, v, COOKIES_DOMAIN)
