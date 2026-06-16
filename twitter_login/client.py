from __future__ import annotations

import json
from io import BufferedIOBase
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, overload

from .api import API
from .auth_manager import AuthManager
from .enums import (
    BatchCompose,
    ConversationControl,
    InstructionType,
    SearchTimelineProduct,
    SearchTimelineQuerySource
)
from .errors import MediaUploadError
from .gql_endpoints import GQLEndpointsManager
from .headers import UserAgent
from .http import HTTPClient
from .media import MediaCategory, MediaUploader
from .models import Tweet, UploadedMedia, build_tweet_media_parameter
from .pagination import PaginatedResult, PaginationContext
from .parsers import (
    get_cursors_from_entries,
    get_cursors_from_replace_entries,
    get_instructions,
    group_entries,
    handle_response_errors,
    parse_entries
)
from .utils import optional_chaining

if TYPE_CHECKING:
    from .models import Tweet, User

logger = getLogger(__name__)


class Client:
    def __init__(self, user_agent: UserAgent, impersonate: str):
        http = HTTPClient(user_agent, impersonate=impersonate)
        self._gql_endpoints_manager = GQLEndpointsManager(http)
        self._api = API(http, self._gql_endpoints_manager.state)
        self._auth_manager = AuthManager(http, self._api)
        self.ratelimits = http.ratelimits_manager

    async def load_cookies_dict(self, cookies: dict[str, str], update_gql_endpoints: bool = True) -> None:
        if not isinstance(cookies, dict):
            raise ValueError(f'Cookies must be dict, not {cookies.__class__.__name__}.')
        await self._auth_manager.login_with_cookies(cookies)
        if update_gql_endpoints:
            await self._gql_endpoints_manager.update_state()

    async def load_cookies(self, path: str, update_gql_endpoints: bool = True) -> None:
        if not isinstance(path, str):
            raise ValueError(f'Path must be str, not {path.__class__.__name__}')
        with open(path, encoding='utf-8') as f:
            cookies = json.load(f)
        await self.load_cookies_dict(cookies, update_gql_endpoints)

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
        reply_to: str | None = None,
        exclude_reply_user_ids: list[str] | None = None,
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

        reply = None
        if reply_to:
            reply = {
                'in_reply_to_tweet_id': reply_to,
                'exclude_reply_user_ids': exclude_reply_user_ids or []
            }

        response = await self._api.gql.CreateTweet(
            tweet_text=text,
            card_uri=None,
            attachment_url=attachment_url,
            reply=reply,
            batch_compose=batch_compose,
            geo=None,
            media=media_param,
            conversation_control={'mode': conversation_control} if conversation_control else None
        )

        payload = response.json()
        handle_response_errors(payload)
        tweet_payload = optional_chaining(
            payload, 'data', 'create_tweet', 'tweet_results', 'result'
        )
        return Tweet._from_payload(tweet_payload, self)

    @overload
    async def search(
        self,
        query: str,
        product: Literal[SearchTimelineProduct.USER],
        count: int = ...,
        cursor: str | None = ...,
        query_source: SearchTimelineQuerySource = ...
    ) -> PaginatedResult[User]:
        ...

    @overload
    async def search(
        self,
        query: str,
        product: Literal[
            SearchTimelineProduct.LIVE,
            SearchTimelineProduct.TOP,
            SearchTimelineProduct.MEDIA,
            SearchTimelineProduct.IMAGE,
            SearchTimelineProduct.VIDEO
        ],
        count: int = ...,
        cursor: str | None = ...,
        query_source: SearchTimelineQuerySource = ...
    ) -> PaginatedResult[Tweet]:
        ...

    async def search(
        self,
        query: str,
        product: SearchTimelineProduct,
        count: int = 20,
        cursor: str | None = None,
        query_source: SearchTimelineQuerySource = SearchTimelineQuerySource.TYPED
    ) -> PaginatedResult[Any]:
        response = await self._api.gql.SearchTimeline(
            rawQuery=query,
            count=count,
            cursor=cursor,
            querySource=query_source,
            product=product
        )
        payload = response.json()
        handle_response_errors(payload)

        instructions = get_instructions(
            payload, 'data', 'search_by_raw_query', 'search_timeline', 'timeline', 'instructions'
        )

        if InstructionType.TIMELINE_ADD_ENTRIES not in instructions:
            return PaginatedResult._empty()

        # Extract TimelineAddEntries entries from instructions
        entries = group_entries(
            instructions.get(InstructionType.TIMELINE_ADD_ENTRIES)[0]['entries']
        )
        replace_entry_instructions = instructions.get(InstructionType.TIMELINE_REPLACE_ENTRY)


        if InstructionType.TIMELINE_ADD_TO_MODULE in instructions:
            add_to_module = instructions[InstructionType.TIMELINE_ADD_TO_MODULE][0]
            module_type = add_to_module['moduleEntryId']

            if module_type.startswith('search-grid'):
                # MEDIA with a cursor
                cursor_top, cursor_bottom = get_cursors_from_replace_entries(
                    replace_entry_instructions
                )
                if 'moduleItems' not in add_to_module:
                    raise ValueError('moduleItems not found in "search-grid"')
                entry_results = add_to_module['moduleItems']

            elif module_type.startswith('list-search'):
                # LIST with a cursor
                return PaginatedResult._empty()  ## TODO List support

            else:
                raise ValueError(f'Unknown moduleEntryId "{module_type}"')


        else:
            if 'search-grid' in entries:
                # MEDIA without a cursor
                cursor_top, cursor_bottom = get_cursors_from_entries(entries)
                items = optional_chaining(entries['search-grid'][0], 'content', 'items')
                if not items:
                    raise ValueError('Items not found in "search-grid"')
                entry_results = group_entries(items)['search-grid-0-tweet']

            elif 'list-search' in entries:
                # LIST without a cursor
                return PaginatedResult._empty()  ## TODO List support

            else:
                if ('cursor-top' in entries or 'cursor-bottom' in entries):
                    # LATEST or TOP without a cursor
                    cursor_top, cursor_bottom = get_cursors_from_entries(entries)

                else:
                    # LATEST or TOP with a cursor
                    cursor_top, cursor_bottom = get_cursors_from_replace_entries(
                        replace_entry_instructions
                    )

                if product == SearchTimelineProduct.USER:
                    entry_results = entries['user']
                else:
                    entry_results = entries['tweet']

        items_iter = parse_entries(self, entry_results)
        ctx = PaginationContext(
            self,
            Client.search,
            cursor_top,
            cursor_bottom,
            # params
            query=query,
            product=product,
            count=count,
            query_source=query_source
        )
        return PaginatedResult(items_iter, ctx)
