from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING, Sequence

from ..enums import MediaCategory, MediaState, SensitiveMediaWarning
from ..errors import MediaUploadError
from ..http import load_json_response
from ..media import SUBTITLE_CATEGORIES, VIDEO_CATEGORIES
from ..utils import sort_enum_values
from .base import BaseModel, optional_subobject

if TYPE_CHECKING:
    from ..client import Client

logger = getLogger(__name__)


@dataclass(slots=True)
class ProcessingInfo:
    state: MediaState
    check_after_secs: str | None = None
    progress_percent: int | None = None
    error: dict | None = None


@dataclass(slots=True)
class Video:
    video_type: str | None = None


@dataclass(slots=True)
class Image:
    image_type: str
    w: int | None = None
    h: int | None = None


@dataclass(slots=True)
class Subtitles:
    subtitle_format: str | None = None


class Metadata:
    def __init__(self) -> None:
        self.__metadata = {}

    def _update(self, metadata):
        for k, v in metadata.items():
            if v is not None:
                self.__metadata[k] = v

    @property
    def alt_text(self) -> dict | None:
        return self.__metadata.get('alt_text')
    @property
    def sensitive_media_warning(self) -> list[SensitiveMediaWarning] | None:
        return self.__metadata.get('sensitive_media_warning')
    @property
    def allow_download_status(self) -> dict | None:
        return self.__metadata.get('allow_download_status')
    @property
    def grok_actions(self) -> dict | None:
        return self.__metadata.get('grok_actions')

    def __repr__(self) -> str:
        text = ', '.join(f'{k}={v}' for k, v in self.__metadata.items())
        return f'{self.__class__.__name__}({text})'


@dataclass(slots=True, repr=False)
class Media(BaseModel, reprs=('media_id', 'category')):
    _client: Client
    category: MediaCategory
    media_id: str
    media_key: str
    size: int

    expires_after_secs: int | None = None
    processing_info: ProcessingInfo | None = None
    video: Video | None = None
    image: Image | None = None
    subtitles: Subtitles | None = None
    metadata: Metadata | None = None
    has_subtitles: bool = False

    def _apply_status(self, payload: dict):
        self.expires_after_secs = payload.get('expires_after_secs')
        self.processing_info = optional_subobject(ProcessingInfo, payload, 'processing_info')
        self.video = optional_subobject(Video, payload, 'video')
        self.image = optional_subobject(Image, payload, 'image')
        self.subtitles = optional_subobject(Subtitles, payload, 'subtitles')

    @classmethod
    def _from_payload(cls, client: Client, payload: dict, category: MediaCategory):
        media_id = payload.get('media_id_string')
        media_key = payload.get('media_key')
        size = payload.get('size')

        instance = cls(client, category, media_id, media_key, size)
        instance._apply_status(payload)
        return instance

    async def update_status(self):
        response = await self._client._api.v11.upload_media_status(media_id=self.media_id)
        payload = load_json_response(response)
        self._apply_status(payload)
        logger.info(payload)

    @property
    def content(self):
        return self.video or self.image or self.subtitles

    async def wait_for_completion(self, timeout = 100):
        if not self.processing_info:
            if not self.content:
                raise MediaUploadError(f'Failed to upload media (media content not found).')
            return

        start_time = time.time()

        while True:
            if not self.processing_info:
                raise MediaUploadError('Processing info not found.')

            state = self.processing_info.state
            if not state:
                raise MediaUploadError('Media state not found.')

            if state == MediaState.FAILED:
                raise MediaUploadError(f'Failed to upload media. Error: {self.processing_info.error}')

            elif state == MediaState.SUCCEEDED:
                break

            elif state in (MediaState.PENDING, MediaState.IN_PROGRESS):
                if time.time() - start_time > timeout:
                    raise MediaUploadError('Upload timeout')
                check_after_secs = self.processing_info.check_after_secs or 1
                await asyncio.sleep(check_after_secs)
                await self.update_status()

            else:
                raise MediaUploadError(f'Unknown uploading state: "{state}"')

    async def create_metadata(
        self,
        *,
        alt_text: str | None = None,
        sensitive_media_warning: Sequence[SensitiveMediaWarning | str] | None = None,
        allow_download: bool | None = None,
        block_grok_edit: bool | None = None
    ) -> None:
        """
        Creates media metadata.
        """
        if self.category in SUBTITLE_CATEGORIES:
            raise ValueError('Cannot create metadata for subtitles.')

        params = {
            'alt_text': None,
            'sensitive_media_warning': None,
            'allow_download_status': None,
            'grok_actions': None
        }

        if alt_text is not None:
            params['alt_text'] = {'text': alt_text}

        if sensitive_media_warning is not None:
            warnings_set = set()
            for v in set(sensitive_media_warning):
                if isinstance(v, SensitiveMediaWarning):
                    warnings_set.add(v)
                    continue
                elif isinstance(v, str):
                    try:
                        warnings_set.add(SensitiveMediaWarning(v))
                        continue
                    except ValueError:
                        pass
                logger.warning(f'Invalid sensitive media warning value: {v}')

            params['sensitive_media_warning'] = sort_enum_values(warnings_set, SensitiveMediaWarning)

        if allow_download is not None:
            params['allow_download_status'] = {'allow_download': str(allow_download).lower()}

        if block_grok_edit is not None:
            params['grok_actions'] = {'block_grok_edit': str(block_grok_edit).lower()}

        await self._client._api.v11.media_metadata_create(media_id=self.media_id, **params)

        if not self.metadata:
            self.metadata = Metadata()
        logger.info(f'Updated media ({self.media_id}) metadata: {self.metadata}')
        self.metadata._update(params)

    async def create_subtitles(self, subtitles: Media):
        """
        Creates video subtitles.
        This method is available only for videos.
        """
        if self.has_subtitles:
            raise RuntimeError(f'Subtitles have already been created for media {self.media_id}.')

        if not self.category in VIDEO_CATEGORIES:
            raise ValueError(f'Subtitle is only supported for video categories.')
        if not subtitles.category in SUBTITLE_CATEGORIES:
            raise ValueError(f'The provided subtitle category "{subtitles.category}" is invalid.')
        subtitle_info = {
            'subtitles': [
                {
                    'media_id': subtitles.media_id,
                    'language_code': 'en',
                    'display_name': 'English'
                }
            ]
        }
        await self._client._api.v11.media_subtitles_create(
            media_id=self.media_id,
            media_category=self.category,
            subtitle_info=subtitle_info
        )
        self.has_subtitles = True
