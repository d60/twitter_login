import json
import random
import re
import time
import uuid
from logging import getLogger

from .api import API
from .castle_token import CastleToken
from .constants import COOKIES_DOMAIN
from .enums import SubtaskID
from .errors import DenyLoginSubtaskError
from .http import HTTPClient
from .login_flow import LoginFlow
from .transaction_id import ClientTransaction

logger = getLogger(__name__)


async def complete_login_flow(flow: LoginFlow, user_identifiers, password, two_fa_handler, email_confirmation_handler):
    while True:
        subtask_ids = {i.get('subtask_id') for i in flow.subtasks}

        if SubtaskID.LOGIN_JS_INSTRUMENTATION_SUBTASK in subtask_ids:
            await flow.LoginJsInstrumentationSubtask()
            await flow.sso_init()

        elif SubtaskID.LOGIN_ENTER_USER_IDENTIFIER_SSO in subtask_ids:
            flow.LoginEnterUserIdentifierSSO(user_identifiers[0])

        elif SubtaskID.LOGIN_ENTER_ALTERNATE_IDENTIFIER_SUBTASK in subtask_ids:
            if len(user_identifiers) < 2:
                raise ValueError('Alternate identifier required.')
            flow.LoginEnterAlternateIdentifierSubtask(user_identifiers[1])

        elif SubtaskID.LOGIN_ENTER_PASSWORD in subtask_ids:
            flow.LoginEnterPassword(password)

        elif SubtaskID.LOGIN_TWO_FACTOR_AUTH_CHALLENGE in subtask_ids:
            try:
                totp = two_fa_handler()
            except Exception as e:
                raise RuntimeError('Failed to get 2FA code') from e
            if not (isinstance(totp, str) and len(totp) == 6):
                raise ValueError('2FA handler must return 6-digit string')
            flow.LoginTwoFactorAuthChallenge(totp)

        elif SubtaskID.LOGIN_ACID in subtask_ids:
            try:
                confirmation_code = email_confirmation_handler()
            except Exception as e:
                raise RuntimeError('Failed to get email confirmation code') from e
            if not (isinstance(confirmation_code, str) and len(confirmation_code) == 8):
                raise ValueError('Email confirmation handler must return 8-digit string')
            flow.LoginAcid(confirmation_code)

        elif SubtaskID.LOGIN_SUCCESS_SUBTASK in subtask_ids:
            logger.info('Login successful')
            break

        elif SubtaskID.DENY_LOGIN_SUBTASK in subtask_ids:
            raise DenyLoginSubtaskError(f'Response: {str(flow.subtasks)}\n\nPlease try again later or try changing the order of user_identifier.')

        else:
            raise ValueError(f'Unknown subtasks: {subtask_ids}')

        logger.info(f'Executing subtasks: {subtask_ids}')
        await flow.execute_subtasks()


class AuthManager:
    def __init__(self, http: HTTPClient, api: API) -> None:
        self.http = http
        self.api = api

    def save_cookies(self, path):
        cookies = self.http.cookies.get_dict(COOKIES_DOMAIN)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f)

    async def ensure_authenticated(self):
        if not self.http.cookies.get('auth_token', domain=COOKIES_DOMAIN):
            raise KeyError('"auth_token" not found in cookies.')
        if not self.http.csrf_token:
            await self.http.get(
                'https://x.com/home',
                params={'prefetchTimestamp': int(time.time()*1000)},
                headers=self.http.build_headers(authorization=False)
            )
            if not self.http.csrf_token:
                raise KeyError('Failed to get ct0 cookie (probably auth_token is invalid).')

    async def initialize_client_transaction(self):
        client_transaction = ClientTransaction()
        await client_transaction.init(self.http, self.http.build_headers(authorization=False))
        self.http.client_transaction = client_transaction

    async def get_guest_token(self):
        response = await self.http.get(
            'https://x.com/i/flow/login',
            headers=self.http.build_headers(authorization=False)
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
        await self.ensure_authenticated()
        await self.initialize_client_transaction()

    async def login(
        self,
        user_identifiers,
        password,
        two_fa_handler,
        email_confirmation_handler,
        castle_fingerprint,
    ) -> None:
        if not user_identifiers:
            raise ValueError('At least one user identifier is required.')

        await self.get_guest_token()
        await self.initialize_client_transaction()
        init_time = int(time.time() * 1000) - random.randint(10000, 20000)
        cuid = uuid.uuid4().hex
        self.http.cookies.set('__cuid', cuid, COOKIES_DOMAIN)

        castle = CastleToken(init_time, cuid, castle_fingerprint)
        flow = LoginFlow(self.http, self.api, castle)

        await flow.start_flow()
        await complete_login_flow(flow, user_identifiers, password, two_fa_handler, email_confirmation_handler)

        await self.ensure_authenticated()
