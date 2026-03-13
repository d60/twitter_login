from __future__ import annotations

from typing import TYPE_CHECKING

from .base import model

if TYPE_CHECKING:
    from ..client import Client


@model(reprs='id')
class User:
    id: str

    @classmethod
    def _from_payload(cls, payload: dict, _client: Client):
        return cls(
            id=payload.get('rest_id')
        )
