import json
import re
import time
import uuid

from .castle_token import CastleToken
from .flow import LoginFlow
from .http import CustomSession
from .transaction_id import ClientTransaction


def default_two_factor_auth_callback(user_identifiers):
    return input(f'Enter 2FA code for {user_identifiers[0]}: ')


class Login:
    def __init__(self):
        self.session = CustomSession(impersonate='chrome142')
        self.guest_token = None

    async def init(self):
        self.session.cookies.clear()
        response = await self.session.get(
            'https://x.com/i/flow/login',
            headers=self.session.build_headers(authorization=False)
        )
        html = response.text
        guest_token_match = re.search(r'gt=([0-9]+);', html)
        if not guest_token_match:
            raise ValueError('guest token not found in html.')
        self.guest_token = guest_token_match.group(1)
        self.session.cookies.set('gt', self.guest_token, '.x.com')

        transaction = ClientTransaction()
        await transaction.init(self.session, self.session.build_headers(authorization=False))
        self.session.transaction = transaction

    async def login(
        self,
        user_identifiers,
        password,
        cookies_file,
        totp_secret = None,
        two_factor_auth_callback = default_two_factor_auth_callback,
        castle_fingerprint = None
    ) -> None:
        await self.init()

        init_time = int(time.time() * 1000) - 15000
        cuid = uuid.uuid4().hex
        self.session.cookies.set('__cuid', cuid, '.x.com')

        castle = CastleToken(init_time, cuid, castle_fingerprint)
        flow = LoginFlow(self.session, self.guest_token, castle)

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
                if totp_secret:
                    from pyotp import TOTP
                    totp = TOTP(totp_secret).now()
                elif two_factor_auth_callback:
                    totp = two_factor_auth_callback(user_identifiers)
                else:
                    ValueError('2FA required but no callback or TOTP secret provided.')
                flow.LoginTwoFactorAuthChallenge(totp)

            elif 'LoginSuccessSubtask' in subtask_ids:
                break

            elif 'DenyLoginSubtask' in subtask_ids:
                raise RuntimeError(str(flow.subtasks))

            else:
                raise ValueError(f'unknown subtasks: {subtask_ids}')

            await flow.execute_subtasks()

        cookies = self.session.cookies.get_dict('.x.com')
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=4)
