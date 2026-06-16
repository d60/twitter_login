import json
import re
import time
from logging import getLogger

from curl_cffi import AsyncSession

from .api import API
from .constants import COOKIES_DOMAIN
from .headers import HeadersConfig
from .http import HTTPClient
from .transaction_id import ClientTransaction
from .transaction_id.utils import get_ondemand_file_url, handle_x_migration_async

logger = getLogger(__name__)


class AuthManager:
    def __init__(self, http: HTTPClient, api: API) -> None:
        self.http = http
        self.api = api

    def save_cookies(self, path):
        cookies = self.http.cookies.get_dict(COOKIES_DOMAIN)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f)

    async def validate_authentication(self):
        """
        Validates authentication cookies.
        """
        if not self.http.cookies.get('auth_token', domain=COOKIES_DOMAIN):
            raise KeyError('"auth_token" not found in cookies.')
        if not self.http.csrf_token:
            # request home to get the csft cookie
            await self.http.get(
                'https://x.com/home',
                headers_config=HeadersConfig.initial_html(),
                params={'prefetchTimestamp': int(time.time()*1000)}
            )
            if not self.http.csrf_token:
                raise KeyError('Failed to get ct0 cookie (probably auth_token is invalid).')

    async def initialize_client_transaction(self):
        session = AsyncSession()
        home_page_response = await handle_x_migration_async(session=session)
        ondemand_file_url = get_ondemand_file_url(response=home_page_response)
        ondemand_file = await session.get(url=ondemand_file_url)
        client_transaction = ClientTransaction(home_page_response, ondemand_file)
        self.http.client_transaction = client_transaction
        logger.info('Initalized ClientTransaction')

    async def get_guest_token(self):
        """
        Extracts guest token from html and sets gt cookie.
        """
        if self.http.guest_token:
            return
        response = await self.http.get(
            'https://x.com/i/jf/onboarding/web',
            headers_config=HeadersConfig.initial_html()
        )
        html = response.text
        guest_token_match = re.search(r'gt=([0-9]+);', html)
        if not guest_token_match:
            raise ValueError('guest token not found in html.')
        guest_token = guest_token_match.group(1)
        self.http.cookies.set('gt', guest_token, COOKIES_DOMAIN)

    async def login_with_cookies(self, cookies):
        if not isinstance(cookies, dict):
            raise ValueError('Cookies must be dict.')
        for k, v in cookies.items():
            if not isinstance(k, str):
                raise ValueError('Cookie name must be str.')
            if not isinstance(v, str):
                raise ValueError('Cookie value must be str.')
            self.http.cookies.set(k, v, COOKIES_DOMAIN)
        await self.validate_authentication()
        await self.initialize_client_transaction()
