from urllib.parse import urlparse

import curl_cffi
from curl_cffi import Response

from .constants import AUTHORIZATION, DEFAULT_HEADERS
from .transaction_id import ClientTransaction


class HTTPError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f'{status_code}: {message}')


class CustomSession(curl_cffi.AsyncSession):
    transaction: ClientTransaction = None

    async def request(
        self,
        method: str,
        url: str,
        *args,
        use_transaction_id: bool = True,
        **kwargs,
    ) -> Response:
        if use_transaction_id and self.transaction:
            transaction_id = self.transaction.generate_transaction_id(method, urlparse(url).path)
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
        return response

    def build_headers(self, authorization = True, extra_headers = None):
        headers = DEFAULT_HEADERS.copy()
        if authorization:
            headers['authorization'] = AUTHORIZATION
        if extra_headers:
            headers |= extra_headers
        return headers
