from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from ..headers import FetchDest, HeadersConfig
from ..jetfuel import JETFUEL_VERSION, JetfuelChunkReader
from .utils import UNSET, remove_unset

if TYPE_CHECKING:
    from ..http import HTTPClient

logger = getLogger(__name__)


class JetfuelClient:
    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    async def jetfuel_request(self, method, url, extra_headers = None, referer = None, data = None, **kwargs) -> JetfuelChunkReader:
        """
        Jetfuel request.
        Returns the jf parser object.
        """
        guest_token = self.http.guest_token
        if not guest_token:
            raise ValueError('Jetfuel request: guest_token is not found.')
        headers = {
            'x-guest-token': guest_token,
            'x-jf-client-theme': 'light',
            'x-jf-v': JETFUEL_VERSION,
            'x-twitter-active-user': 'yes'
        }
        if extra_headers:
            headers |= extra_headers

        if data:
            data = remove_unset(data)

        headers_config = HeadersConfig(
            dest=FetchDest.FETCH,
            csrf_token=False,
            referer=referer,
            extra_headers=headers
        )
        logger.info(f'Jetfuel Request: {method} : {url}')
        response = await self.http.request(
            method,
            url,
            headers_config,
            data=data,
            **kwargs
        )
        content = response.content
        return JetfuelChunkReader(content)

    async def begin_login(self, *, username_or_email, castle_token) -> JetfuelChunkReader:
        data = {
            'username_or_email': username_or_email,
            '$castle_token': castle_token
        }
        return await self.jetfuel_request(
            'POST',
            'https://x.com/i/jfapi/onboarding/web/actions/begin_login',
            referer='https://x.com/',
            data=data
        )

    async def login_enter_password(self, *, username, email, password, session_token, castle_token) -> JetfuelChunkReader:
        data = {
            # either email or username
            'email': email or UNSET,
            'username': username or UNSET,
            'password': password,
            'session_token': session_token,
            '$castle_token': castle_token
        }
        return await self.jetfuel_request(
            'POST',
            'https://x.com/i/jfapi/onboarding/web/actions/login_enter_password',
            referer='https://x.com/i/jf/onboarding/web',
            data=data
        )