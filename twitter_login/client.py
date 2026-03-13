import json
import os
from io import BufferedIOBase
from logging import getLogger
from pathlib import Path
from typing import Callable, Sequence

from .api import API
from .auth_manager import AuthManager
from .enums import BatchCompose, ConversationControl
from .errors import MediaUploadError
from .gql_endpoints import GQLEndpointsManager
from .http import HTTPClient
from .login_handlers import default_email_confirmation_handler, default_two_fa_handler
from .media import MediaCategory, MediaUploader
from .models import Tweet, UploadedMedia, build_tweet_media_parameter
from .utils import optional_chaining

logger = getLogger(__name__)


class Client:
    def __init__(self):
        http = HTTPClient(impersonate='chrome142')
        self._gql_endpoints_manager = GQLEndpointsManager(http)
        self._api = API(http, self._gql_endpoints_manager.state)
        self._auth_manager = AuthManager(http, self._api)
        self.ratelimits = http.ratelimits_manager

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

    async def login_with_cookies(self, cookies: dict[str, str]) -> None:
        await self._auth_manager.login_with_cookies(cookies)
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
    ) -> UploadedMedia:
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
        media = UploadedMedia._from_payload(finalize_payload, self, media_category)

        if not media.processing_info:
            if not media.content:
                raise MediaUploadError(f'Failed to upload media: "{finalize_payload}"')
            return media

        if wait_for_completion:
            await media.wait_for_completion(timeout)
        return media

    async def create_tweet(
        self,
        text: str = '',
        # card = None,
        attachment_url: str | None = None,
        # reply_to: str | None = None,
        # exclude_reply_user_ids: list[str] | None = None,
        batch_compose: BatchCompose = BatchCompose.SINGLE_TWEET,
        # geo = None,
        media: list[UploadedMedia] | None = None,
        tagged_users: list[str] | None = None,
        conversation_control: ConversationControl | None = None
    ):
        if batch_compose == BatchCompose.SINGLE_TWEET:
            batch_compose = None

        media_param = build_tweet_media_parameter(
            media or [], tagged_users or []
        )

        response = await self._api.gql.CreateTweet(
            tweet_text=text,
            card_uri=None,
            attachment_url=attachment_url,
            reply=None,
            batch_compose=batch_compose,
            geo=None,
            media=media_param,
            conversation_control={'mode': conversation_control} if conversation_control else None
        )

        # TODO error handling
        payload = response.json()
        tweet_payload = optional_chaining(
            payload, 'data', 'create_tweet', 'tweet_results', 'result'
        )
        return Tweet._from_payload(tweet_payload, self)
