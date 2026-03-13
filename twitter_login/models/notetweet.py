import base64

from .base import model
from .lazy import LazyMixin
from .tweet_entities import TweetEntitiesMixin


@model(reprs='id')
class NoteTweet(TweetEntitiesMixin, LazyMixin):
    text: str
    id_base64: str

    @classmethod
    def _from_payload(cls, payload):
        instance = cls(
            text=payload.get('text'),
            id_base64=payload.get('id')
        )
        entity_set = payload.get('entity_set', {})
        instance._set_sources_from_entities(entity_set)
        return instance

    @property
    def id(self) -> str:
        id_text = base64.b64decode(self.id_base64).decode()
        return id_text.removeprefix('NoteTweet:')
