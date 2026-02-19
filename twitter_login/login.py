import os
import re
import time
import uuid

from .api import API
from .castle_token import CastleToken
from .constants import COOKIES_DOMAIN
from .flow import LoginFlow
from .http import HTTPClient
from .login_handlers import default_email_confirmation_handler, default_two_fa_handler
from .transaction_id import ClientTransaction


class Client:
    def __init__(self):
        self.http = HTTPClient(impersonate='chrome142')
        self.api = API(self.http)

    async def init(self):
        self.http.cookies.clear()
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

        client_transaction = ClientTransaction()
        await client_transaction.init(self.http, self.http.build_headers(authorization=False))
        self.http.client_transaction = client_transaction

    async def login(
        self,
        user_identifiers,
        password,
        cookies_file,
        two_fa_handler = default_two_fa_handler,
        email_confirmation_handler = default_email_confirmation_handler,
        castle_fingerprint = None
    ) -> None:
        if os.path.exists(cookies_file):
            self.http.load_cookies(cookies_file)
            # TODO cookies validation
            return

        await self.init()
        init_time = int(time.time() * 1000) - 15000
        cuid = uuid.uuid4().hex
        self.http.cookies.set('__cuid', cuid, COOKIES_DOMAIN)

        castle = CastleToken(init_time, cuid, castle_fingerprint)
        flow = LoginFlow(self.http, self.api, castle)

        await flow.init_flow()

        while True:
            subtask_ids = [i['subtask_id'] for i in flow.subtasks]

            if 'LoginJsInstrumentationSubtask' in subtask_ids:
                await flow.LoginJsInstrumentationSubtask()
                await flow.sso_init()

            elif 'LoginEnterUserIdentifierSSO' in subtask_ids:
                flow.LoginEnterUserIdentifierSSO(user_identifiers[0])

            elif 'LoginEnterAlternateIdentifierSubtask' in subtask_ids:
                if len(user_identifiers) < 2:
                    raise ValueError('Alternate identifier required.')
                flow.LoginEnterAlternateIdentifierSubtask(user_identifiers[1])

            elif 'LoginEnterPassword' in subtask_ids:
                flow.LoginEnterPassword(password)

            elif 'LoginTwoFactorAuthChallenge' in subtask_ids:
                try:
                    totp = two_fa_handler()
                except Exception as e:
                    raise RuntimeError('Failed to get 2FA code') from e
                flow.LoginTwoFactorAuthChallenge(totp)

            elif 'LoginAcid' in subtask_ids:
                try:
                    confirmation_code = email_confirmation_handler()
                except Exception as e:
                    raise RuntimeError('Failed to get email confirmation code') from e
                flow.LoginAcid(confirmation_code)

            elif 'LoginSuccessSubtask' in subtask_ids:
                break

            elif 'DenyLoginSubtask' in subtask_ids:
                raise RuntimeError(str(flow.subtasks))

            else:
                raise ValueError(f'Unknown subtasks: {subtask_ids}')

            await flow.execute_subtasks()

        self.http.save_cookies(cookies_file)
