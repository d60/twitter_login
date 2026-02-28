from __future__ import annotations

from enum import Enum
from typing import NamedTuple, Type
from urllib.parse import urlparse


class FetchDest(Enum):
    DOCUMENT = 'document'
    JAVASCRIPT = 'script'
    IMAGE = 'image'
    FETCH = 'empty'
    VIDEO = 'video'


class FetchSite(Enum):
    SAME_ORIGIN = 'same-origin'
    SAME_SITE= 'same-site'
    CROSS_SITE = 'cross-site'
    NONE = 'none'


class FetchMode(Enum):
    NAVIGATE = 'navigate'
    CORS = 'cors'
    NO_CORS = 'no-cors'


class FetchUser(Enum):
    TRUE = '?1'
    FALSE = None


class UpgradeInsecureRequests(Enum):
    TRUE = '1'
    FALSE = None


ACCEPT_MAPPING = {
    FetchDest.DOCUMENT: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    FetchDest.JAVASCRIPT: '*/*',
    FetchDest.IMAGE: 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    FetchDest.FETCH: '*/*',
    FetchDest.VIDEO: '*/*'
}

PRIORITY_MAPPING = {
    FetchDest.DOCUMENT: 'u=0, i',
    FetchDest.JAVASCRIPT: 'u=1',
    FetchDest.IMAGE: 'i',
    FetchDest.VIDEO: 'i',
    FetchDest.FETCH: 'u=1, i'
}


class UserAgent(NamedTuple):
    ch_ua: str
    ch_ua_mobile: str
    ch_ua_platform: str
    user_agent: str


UA_WINDOWS_CHROME_142 = UserAgent(
    ch_ua='"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    ch_ua_mobile="?0",
    ch_ua_platform='"Windows"',
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
)


# 仕様間違ってたら教えてください
class HeadersContext:
    def __init__(self, domain: str, url: str, method: str, dest: FetchDest, is_user_access: bool, is_cors: bool) -> None:
        self.domain = domain
        self.origin_ = f'https://{domain}'
        self.url = url
        self.method = method.upper()
        self.dest = dest

        if is_user_access is None:
            is_user_access = dest == FetchDest.DOCUMENT
        self.is_user_access = is_user_access

        self.is_cors = is_cors


    def fetch_site(self) -> FetchSite:
        if self.is_user_access:
            # 直アクセスの時はnone
            return FetchSite.NONE
        parsed_url = urlparse(self.url)
        hostname = parsed_url.hostname
        if hostname == self.domain:
            # ドメイン完全一致でsame-origin
            return FetchSite.SAME_ORIGIN
        if hostname.endswith(f'.{self.domain}'):
            # ルートドメイン一致でsame-size
            return FetchSite.SAME_SITE
        # 不一致でcross-site
        return FetchSite.CROSS_SITE

    def origin(self) -> str | None:
        if self.method == 'POST':
            # POSTなら必ず必要
            return self.origin_
        if self.fetch_site() in [FetchSite.SAME_ORIGIN, FetchSite.NONE]:
            return None
        # GETかつsame-site/cross-siteなら必要
        return self.origin_

    def fetch_mode(self) -> FetchMode:
        if self.dest == FetchDest.DOCUMENT:
            return FetchMode.NAVIGATE

        if self.is_cors is not None:
            # is_corsがあったら強制
            if self.is_cors:
                return FetchMode.CORS
            return FetchMode.NO_CORS

        if self.dest == FetchDest.FETCH:
            # Fetch (empty)ならcors
            return FetchMode.CORS

        if self.dest == FetchDest.JAVASCRIPT:
            # twitterではたいていjavascriptの時はcorsになる
            # no-corsにしたいならis_cors=Falseを渡す
            return FetchMode.CORS

        # その他imageなどno-cors
        return FetchMode.NO_CORS

    def fetch_user(self):
        if self.is_user_access:
            return FetchUser.TRUE
        return FetchUser.FALSE

    def upgrade_insecure_requests(self):
        if self.dest == FetchDest.DOCUMENT:
            return UpgradeInsecureRequests.TRUE
        return UpgradeInsecureRequests.FALSE

    def accept(self):
        return ACCEPT_MAPPING.get(self.dest, '*/*')

    def priority(self):
        return PRIORITY_MAPPING.get(self.dest, 'u=1, i')


class HeadersBuilder:
    def __init__(self, domain: str = 'x.com', user_agent: UserAgent = UA_WINDOWS_CHROME_142) -> None:
        self.domain = domain
        self.user_agent = user_agent

    def ua_headers(self):
        return {
            'user-agent': self.user_agent.user_agent,
            'sec-ch-ua': self.user_agent.ch_ua,
            'sec-ch-ua-mobile': self.user_agent.ch_ua_mobile,
            'sec-ch-ua-platform': self.user_agent.ch_ua_platform
        }

    def build(self, url: str, method: str, dest: FetchDest, is_user_access: bool = None, is_cors: bool = None):
        context = HeadersContext(self.domain, url, method, dest, is_user_access, is_cors)
        return {
            **self.ua_headers(),
            'sec-fetch-dest': dest.value,
            'sec-fetch-mode': context.fetch_mode().value,
            'sec-fetch-site': context.fetch_site().value,
            'sec-fetch-user': context.fetch_user().value,
            'upgrade-insecure-requests': context.upgrade_insecure_requests().value,
            'accept': context.accept(),
            'origin': context.origin(),
            'priority': context.priority()
        }


class HeadersConfig(NamedTuple):
    dest: FetchDest
    is_user_access: bool | None = None
    is_cors: bool | None = None
    authorization: bool = True
    csrf_token: bool = True
    transaction_id: bool = True
    json: bool = False
    referer: str | None = None
    extra_headers: dict | None = None

    @classmethod
    def general_api(cls: Type[HeadersConfig], referer: str | None = None, extra_headers: dict | None = None):
        # Headers config preset for general API request
        return cls(
            dest=FetchDest.FETCH,
            json=True,
            referer=referer,
            extra_headers=extra_headers
        )

    @classmethod
    def initial_html(cls: Type[HeadersConfig]):
        return cls(
            dest=FetchDest.DOCUMENT,
            is_user_access=True,
            authorization=False,
            csrf_token=False,
            transaction_id=False
        )

    @classmethod
    def general_js(cls: Type[HeadersConfig], referer: str = 'https://x.com/'):
        return cls(
            dest=FetchDest.JAVASCRIPT,
            is_cors=True,
            authorization=False,
            csrf_token=False,
            transaction_id=False,
            referer=referer
        )
