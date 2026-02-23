from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..http import HTTPClient


class V11:
    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    async def onboarding_task(self, data, params = None):
        headers = self.http.build_headers(json=True, extra_headers={
            'x-twitter-active-user': 'yes',
            'x-twitter-client-language': 'en',
            'x-guest-token': self.http.guest_token
        })
        return await self.http.post(
            'https://api.x.com/1.1/onboarding/task.json',
            params=params,
            json=data,
            headers=headers
        )

    async def onboarding_sso_init(self, provider):
        headers = self.http.build_headers(json=True, extra_headers={
            'x-twitter-active-user': 'yes',
            'x-twitter-client-language': 'en',
            'x-guest-token': self.http.guest_token
        })
        data = {'provider': provider}
        return await self.http.post(
            'https://api.x.com/1.1/onboarding/sso_init.json',
            json=data,
            headers=headers
        )

    async def user_state(self):
        headers = self.http.build_headers()
        return await self.http.get(
            'https://api.x.com/help-center/forms/api/prod/user_state.json',
            headers=headers
        )
