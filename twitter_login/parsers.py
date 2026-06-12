from collections import defaultdict
from functools import wraps
from logging import getLogger
from typing import Callable

from .errors import ResponseError
from .models import Tweet, User
from .utils import optional_chaining

logger = getLogger(__name__)

# Response parser utilities


def entry_id_to_type(entry_id: str) -> str:
    # tweet-00000000 -> tweet
    # cursor-top-00000000 -> cursor-top
    return entry_id.rsplit('-', 1)[0]


def get_instructions(response: dict, *path_to_instructions) -> dict[str, list[dict]]:
    """
    Extracts instructions from a response dictionary and groups them by type.
    path_to_instructions:
        A sequence of keys to navigate to the instructions.
    """
    instructions = optional_chaining(response, *path_to_instructions)
    if not instructions:
        raise ValueError('instructions not found in response.')
    return group_instructions(instructions)


def group_list_by_key(l: list[dict], key: Callable) -> dict[str, list[dict]]:
    """
    Groups dicts by a specific key.
    Example:
        X = [
            {'key': 'A', 'value': 1},
            {'key': 'A', 'value': 2},
            {'key': 'B', 'value': 1},
            {'key': 'B', 'value': 2}
        ]
        group_list_by_key(X, 'key')
        >>> {
            'A': [
                {'key': 'A', 'value': 1},
                {'key': 'A', 'value': 2}
            ],
            'B': [
                {'key': 'B', 'value': 1},
                {'key': 'B', 'value': 2}
            ]
        }
    """
    m = defaultdict(list)
    for elem in l:
        k = key(elem)
        m[k].append(elem)
    return m


def group_instructions(raw_instructions: list[dict]) -> dict[str, list[dict]]:
    """
    Groups instructions by type
    """
    return group_list_by_key(raw_instructions, lambda x: x.get('type'))


def group_entries(raw_entries: list[dict]) -> dict[str, list[dict]]:
    """
    Groups entries by entry type
    """
    return group_list_by_key(
        raw_entries,
        lambda x: entry_id_to_type(x['entryId'])
    )


def get_cursors_from_entries(grouped_entries: dict[str, list[dict]]) -> tuple[str | None, str | None]:
    """
    Extracts (cursor-top, cursor-bottom) from the TimelineAddEntries instruction.
    """
    return tuple(
        (
            grouped_entries[type][0].get('content', {}).get('value')
            if type in grouped_entries else None
        )
        for type in ('cursor-top', 'cursor-bottom')
    )


def get_cursors_from_replace_entries(replace_entry_instructions):
    """
    Extracts (cursor-top, cursor-bottom) from list of ReplaceEntry instructions.
    """
    cursor_top = cursor_bottom = None

    for i in replace_entry_instructions:
        entry = i.get('entry')
        if not entry:
            continue
        entry_id = entry.get('entryId')
        if not entry_id:
            continue

        type = entry_id_to_type(entry_id)
        if type == 'cursor-top':
            cursor_top = entry.get('content', {}).get('value')
        elif type == 'cursor-bottom':
            cursor_bottom = entry.get('content', {}).get('value')

    return cursor_top, cursor_bottom

# Entries parsers
# @register_parser('entry-type') registers a parser for 'entry-type'.

parsers = {}


def register_parser(type: str):
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        parsers[type] = wrapper
        return wrapper
    return deco


def _parse_tweet_base(client, payload):
    if not payload:
        logger.warning('Failed to parse a tweet entry. Tweet data not found.')
        return

    if 'tweet' in payload:
        # handle TweetWithVisibilityResults
        payload = payload['tweet']

    return Tweet._from_payload(payload, client)


@register_parser('tweet')
def parse_tweet(client, entry):
    payload = optional_chaining(
        entry, 'content', 'itemContent', 'tweet_results', 'result'
    )
    return _parse_tweet_base(client, payload)


@register_parser('search-grid-0-tweet')
def parse_search_grid_0_tweet(client, entry):
    # media searching result
    payload = optional_chaining(
        entry, 'item', 'itemContent', 'tweet_results', 'result'
    )
    return _parse_tweet_base(client, payload)


@register_parser('user')
def parse_user(client, entry):
    payload = optional_chaining(
        entry, 'content', 'itemContent', 'user_results', 'result'
    )
    if not payload:
        logger.warning('Failed to parse a user entry. User data not found.')
    return User._from_payload(payload, client)


def parse_entries(client, entries):
    """
    Parses entries list.
    Yields parsed etry object.
    """

    for entry in entries:
        entry_id = entry.get('entryId')
        if not entry_id:
            logger.info('EntryId not found. Skipped an entry.')
            continue
        type = entry_id_to_type(entry_id)
        parser = parsers.get(type)
        if not parser:
            logger.info(f'The parser for entry type "{type}" is not registered. Skipped an entry.')
            continue

        parsed = parser(client, entry)
        if not parsed:
            continue

        yield parsed


def handle_response_errors(response):
    """
    Handles the 'errors' key in response.
    """
    if not isinstance(response, dict):
        raise ValueError(f'Unknown response type: `{response.__class__.__name__}`')

    if 'errors' in response:
        raise ResponseError(response['errors'])
