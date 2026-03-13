from dataclasses import dataclass
from typing import ClassVar

from .base import model
from .lazy import Lazy


@model(reprs='url')
class URL:
    display_url: str
    expanded_url: str
    url: str
    indices: list[int]

    @classmethod
    def _from_payload(cls, payload):
        return cls(
            display_url=payload.get('display_url'),
            expanded_url=payload.get('expanded_url'),
            url=payload.get('url'),
            indices=payload.get('indices')
        )


@model(reprs='text')
class Hashtag:
    text: str
    indices: list[int]

    @classmethod
    def _from_payload(cls, payload: dict):
        return cls(
            text=payload.get('text'),
            indices=payload.get('indices')
        )


@model(reprs='text')
class Symbol:
    text: str
    indices: list[int]

    @classmethod
    def _from_payload(cls, payload: dict):
        return cls(
            text=payload.get('text'),
            indices=payload.get('indices')
        )


@model(reprs='id')
class Mention:
    id: str
    name: str
    screen_name: str
    indices: list[int]

    @classmethod
    def _from_payload(cls, payload: dict):
        return cls(
            id=payload.get('id_str'),
            name=payload.get('name'),
            screen_name=payload.get('screen_name'),
            indices=payload.get('indices')
        )


@dataclass(repr=False, slots=True)
class TweetEntitiesMixin:
    urls: ClassVar[list[URL]] = Lazy(URL)
    hashtags: ClassVar[list[Hashtag]] = Lazy(Hashtag)
    symbols: ClassVar[list[Symbol]] = Lazy(Symbol)
    mentions: ClassVar[list[Mention]] = Lazy(Mention)

    def _set_sources_from_entities(self, entities: dict):
        self.urls = entities.get('urls', [])
        self.hashtags = entities.get('hashtags', [])
        self.symbols = entities.get('symbols', [])
        self.mentions = entities.get('user_mentions', [])
