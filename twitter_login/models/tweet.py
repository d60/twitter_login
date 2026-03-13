from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Type

from ..utils import optional_chaining, safe_convert
from .base import model
from .card import Card
from .lazy import Lazy, LazyMixin
from .notetweet import NoteTweet
from .tweet_entities import URL, Hashtag, Mention, Symbol, TweetEntitiesMixin
from .user import User

if TYPE_CHECKING:
    from ..client import Client


@model(reprs='id')
class Tweet(TweetEntitiesMixin, LazyMixin):
    _client: Client
    id: str
    view_count: int
    bookmark_count: int
    bookmarked: bool
    created_at: str
    favorite_count: int
    favorited: bool
    text: str
    is_quote_status: bool
    in_reply_to_screen_name: str | None
    in_reply_to_user_id: str | None
    lang: str
    quote_count: int
    reply_count: int
    retweet_count: int
    retweeted: bool
    user_id: str
    source: str

    user: ClassVar[User | None] = Lazy(
        User,
        kwargs_factory=lambda x: {'_client': x._client}
    )
    note_tweet: ClassVar[NoteTweet | None] = Lazy(NoteTweet)
    card: ClassVar[Card | None] = Lazy(Card)

    @classmethod
    def _from_payload(cls: Type['Tweet'], payload: dict, client: Client, user: User | None = None):
        legacy = payload.get('legacy', {})
        views = payload.get('views', {})

        instance = cls(
            _client=client,
            id=payload.get('rest_id'),
            view_count=safe_convert(views.get('count', 0), int),
            bookmark_count=legacy.get('bookmark_count'),
            bookmarked=legacy.get('bookmarked'),
            created_at=legacy.get('created_at'),
            favorite_count=legacy.get('favorite_count'),
            favorited=legacy.get('favorited'),
            text=legacy.get('full_text'),
            is_quote_status=legacy.get('is_quote_status'),
            in_reply_to_screen_name=legacy.get('in_reply_to_screen_name'),
            in_reply_to_user_id=legacy.get('in_reply_to_user_id_str'),
            lang=legacy.get('lang'),
            quote_count=legacy.get('quote_count'),
            reply_count=legacy.get('reply_count'),
            retweet_count=legacy.get('retweet_count'),
            retweeted=legacy.get('retweeted'),
            user_id=legacy.get('user_id_str'),
            source=payload.get('source')
        )

        if not user:
            user = optional_chaining(payload, 'core', 'user_results', 'result')

        instance.user = user

        note_tweet = optional_chaining(payload, 'note_tweet', 'note_tweet_results', 'result')

        instance.note_tweet = note_tweet
        instance.card = payload.get('card')

        entities = legacy.get('entities', {})
        instance._set_sources_from_entities(entities)

        return instance

    def _fallback_to_note(self, attr_name):
        if self.note_tweet:
            return getattr(self.note_tweet, attr_name)
        return getattr(self, attr_name)

    @property
    def full_text(self) -> str:
        return self._fallback_to_note('text')

    @property
    def full_urls(self) -> list[URL]:
        return self._fallback_to_note('urls')

    @property
    def full_hashtags(self) -> list[Hashtag]:
        return self._fallback_to_note('hashtags')

    @property
    def full_symbols(self) -> list[Symbol]:
        return self._fallback_to_note('symbols')

    @property
    def full_mentions(self) -> list[Mention]:
        return self._fallback_to_note('mentions')
