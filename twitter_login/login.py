import json
import re
import time
import uuid

from .castle_token import CastleToken
from .flow import LoginFlow
from .http import CustomSession, build_headers
from .transaction_id import ClientTransaction


class Login:
    def __init__(self):
        self.session = CustomSession(impersonate='chrome142', raise_for_status=True)
        self.guest_token = None

    async def init(self):
        self.session.cookies.clear()
        response = await self.session.get(
            'https://x.com/i/flow/login',
            headers=build_headers(authorization=False)
        )
        html = response.text
        guest_token_match = re.search(r'gt=([0-9]+);', html)
        if not guest_token_match:
            raise ValueError('guest token not found in html.')
        self.guest_token = guest_token_match.group(1)
        self.session.cookies.set('gt', self.guest_token, '.x.com')

        transaction = ClientTransaction()
        await transaction.init(self.session, build_headers(authorization=False))
        self.session.transaction = transaction

    async def login(self, user_identifiers, password, cookies_file, castle_fingerprint = None):
        await self.init()

        init_time = int(time.time() * 1000) - 15000
        cuid = uuid.uuid4().hex
        self.session.cookies.set('__cuid', cuid, '.x.com')

        castle = CastleToken(init_time, cuid, castle_fingerprint)
        flow = LoginFlow(self.session, self.guest_token, castle)
        await flow.complete(user_identifiers, password)

        cookies = self.session.cookies.get_dict('.x.com')
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=4)
