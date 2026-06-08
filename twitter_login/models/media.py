from __future__ import annotations

from typing import TYPE_CHECKING, Type

from .base import model

if TYPE_CHECKING:
    from ..client import Client

# TODO media model
@model(reprs='id')
class Media:
    _client: Client
    id: str
    media_url: str
    video_info: dict # TODO remove this

    @classmethod
    def _from_payload(cls: Type['Media'], payload: dict, client: Client):
       instance = cls(
            _client=client,
            id=payload.get('id_str'),
            media_url=payload.get('media_url_https'),
            video_info=payload.get('video_info')
        )
       return instance
