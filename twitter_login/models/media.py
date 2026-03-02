from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING
import time
from ..errors import MediaUploadError
from logging import getLogger

from ..enums import MediaState, MediaCategory
from ..http import load_json_response
from .base import BaseModel

if TYPE_CHECKING:
    from ..client import Client

logger = getLogger(__name__)


def optional_subobject(cls, payload, field_name):
    data = payload.get(field_name)
    if data is None:
        return
    return cls(**data)


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


@dataclass(slots=True, repr=False)
class Media(BaseModel, reprs='media_id'):
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
        response = await self._client._api.v11.upload_media_status(self.media_id)
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
