import json
import os
from io import BufferedIOBase
from logging import getLogger
from pathlib import Path
from typing import Callable, Sequence

from .api import API
from .auth_manager import AuthManager
from .errors import MediaUploadError
from .gql_endpoints import GQLEndpointsManager
from .http import HTTPClient
from .login_handlers import default_email_confirmation_handler, default_two_fa_handler
from .media import MediaCategory, MediaUploader
from .models import Media

logger = getLogger(__name__)


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

    async def upload_media(
        self,
        source: str | Path | bytes | BufferedIOBase,
        media_category: MediaCategory,
        mimetype: str | None = None,
        concurrency: int = 6,
        enable_video_duration: bool = True,
        wait_for_completion: bool = True,
        timeout: int = 100
    ) -> Media:
        """
        Uploads media
        """
        uploader = MediaUploader(
            self._api, source, media_category,
            mimetype=mimetype,
            concurrency=concurrency,
            enable_video_duration=enable_video_duration
        )
        finalize_payload = await uploader.upload()
        logger.info(f'Upload finalized: {finalize_payload}')
        media = Media._from_payload(self, finalize_payload, media_category)

        if not media.processing_info:
            if not media.content:
                raise MediaUploadError(f'Failed to upload media: "{finalize_payload}"')
            return media

        if wait_for_completion:
            await media.wait_for_completion(timeout)
        return media