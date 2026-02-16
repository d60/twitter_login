from urllib.parse import urlparse

import curl_cffi
from curl_cffi import Response

from .constants import AUTHORIZATION, DEFAULT_HEADERS
from .transaction_id import ClientTransaction


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
            transaction_id = self.transaction.generate_transaction_id(
                method,
                urlparse(url).path
            )
            headers = kwargs.get('headers') or {}
            headers['x-client-transaction-id'] = transaction_id
            kwargs['headers'] = headers

        return await super().request(method, url, *args, **kwargs)


def build_headers(authorization = True, extra_headers = None):
    headers = DEFAULT_HEADERS.copy()
    if authorization:
        headers['authorization'] = AUTHORIZATION
    if extra_headers:
        headers |= extra_headers
    return headers
