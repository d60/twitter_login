import json
from logging import INFO, getLogger
from typing import Any
from urllib.parse import urlparse

import curl_cffi
from curl_cffi import Response

from .constants import AUTHORIZATION, COOKIES_DOMAIN
from .errors import HTTPError
from .headers import HeadersBuilder, HeadersConfig
from .ratelimits import RatelimitsManager
from .transaction_id import ClientTransaction

logger = getLogger(__name__)
headers_logger = getLogger('headers_log')


class HTTPClient(curl_cffi.AsyncSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ratelimits_manager = RatelimitsManager()
        self.client_transaction: ClientTransaction | None = None
        self.headers_builder = HeadersBuilder()

    async def request(
        self,
        method: str,
        url: str,
        headers_config: HeadersConfig,
        **kwargs,
    ) -> Response:
        if 'headers' in kwargs:
            raise ValueError('Use headers_config instead of headers.')

        headers = self.build_headers(url, method, headers_config)
        logger.info(f'Build headers for {method} {url[:100]}...')
        if headers_logger.isEnabledFor(INFO):
            headers_logger.info(
                'Method: %s URL: %s\n\n%s\n\n', method, url,
                json.dumps(headers, indent=4, ensure_ascii=False)
            )

        response: Response = await super().request(method, url, headers=headers, **kwargs)
        status_code = response.status_code
        if 400 <= status_code < 600:
            MESSAGE_MAX_LENGTH = 2000
            try:
                message = response.text[:MESSAGE_MAX_LENGTH]
            except:
                message = ''
            raise HTTPError(status_code, message)

        self.ratelimits_manager.update(url, response.headers)
        return response

    async def get(self, url: str, headers_config: HeadersConfig, **kwargs) -> Response:
        return await self.request('GET', url, headers_config, **kwargs)

    async def post(self, url: str, headers_config: HeadersConfig, **kwargs) -> Response:
        return await self.request('POST', url, headers_config, **kwargs)

    def build_headers(self, url, method, config: HeadersConfig):
        headers = self.headers_builder.build(
            url, method, config.dest, config.is_user_access, config.is_cors
        )
        if config.authorization:
            headers['authorization'] = AUTHORIZATION
        if config.csrf_token:
            csrf_token = self.csrf_token
            if csrf_token is not None:
                headers['x-csrf-token'] = csrf_token
        if config.transaction_id and self.client_transaction:
            transaction_id = self.client_transaction.generate_transaction_id(method, urlparse(url).path)
            headers['x-client-transaction-id'] = transaction_id
        if config.json:
            headers['content-type'] = 'application/json'
        if config.referer:
            headers['referer'] = config.referer
        if config.extra_headers:
            headers.update(config.extra_headers)
        return headers

    @property
    def csrf_token(self):
        return self.cookies.get('ct0', domain=COOKIES_DOMAIN)

    @property
    def guest_token(self):
        return self.cookies.get('gt', domain=COOKIES_DOMAIN)


def load_json_response(response: Response) -> dict | list | Any:
    try:
        return response.json()
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f'Invalid JSON response. Response: {response}, Body: {response.text[:200]}'
        ) from e
