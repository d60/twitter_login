import json
import os
from typing import Callable, Sequence

from .api import API
from .auth_manager import AuthManager
from .gql_endpoints import GQLEndpointsManager
from .http import HTTPClient
from .login_handlers import default_email_confirmation_handler, default_two_fa_handler


class Client:
    def __init__(self):
        http = HTTPClient(impersonate='chrome142')
        self._gql_endpoints_manager = GQLEndpointsManager(http)
        self._api = API(http, self._gql_endpoints_manager.state)
        self._auth_manager = AuthManager(http, self._api)
        self.ratelimits = http.ratelimits_manager

    async def login_with_cookies(self, cookies: dict[str, str]) -> None:
        await self._auth_manager.login_with_cookies(cookies)
        await self._gql_endpoints_manager.update_state()

    async def login(
        self,
        user_identifiers: Sequence[str],
        password: str,
        cookies_file: str,
        *,
        two_fa_handler: Callable[[], str] = default_two_fa_handler,
        email_confirmation_handler: Callable[[], str] = default_email_confirmation_handler,
        castle_fingerprint = None,
    ) -> None:
        if os.path.exists(cookies_file):
            with open(cookies_file, encoding='utf-8') as f:
                try:
                    cookies = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(f'Failed loading cookies from "{cookies_file}"') from e
            await self._auth_manager.login_with_cookies(cookies)
        else:
            await self._auth_manager.login(
                user_identifiers,
                password,
                two_fa_handler,
                email_confirmation_handler,
                castle_fingerprint
            )
            self._auth_manager.save_cookies(cookies_file)
        await self._gql_endpoints_manager.update_state()

    def save_cookies(self, path):
        self._auth_manager.save_cookies(path)
