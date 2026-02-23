import json
from typing import Any
from urllib.parse import urlparse

import curl_cffi
from curl_cffi import Response

from .constants import AUTHORIZATION, COOKIES_DOMAIN, DEFAULT_HEADERS
from .errors import HTTPError
from .ratelimits import RatelimitsManager
from .transaction_id import ClientTransaction


class HTTPClient(curl_cffi.AsyncSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ratelimits_manager = RatelimitsManager()
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

        self.ratelimits_manager.update(url, response.headers)
        return response

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
            headers['content-type'] = 'application/json'
        return headers

    @property
    def csrf_token(self):
        return self.cookies.get('ct0', domain=COOKIES_DOMAIN)

    @property
    def guest_token(self):
        return self.cookies.get('gt', domain=COOKIES_DOMAIN)


def parse_json_response(response: Response) -> dict | list | Any:
    try:
        return response.json()
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f'Invalid JSON response. Status: {response.status_code}, Body: {response.text[:200]}'
        ) from e
