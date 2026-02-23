import re
from collections import defaultdict
from logging import getLogger
from typing import AsyncGenerator, Callable, TypedDict

import chompjs
from typing_extensions import NotRequired

logger = getLogger(__name__)

PATTERN_MAPPING = {
    'id': r'(?P<queryId>[a-zA-Z0-9_-]{22})',
    'name': r'(?P<operationName>[a-zA-Z0-9_]+)',
    'meta': r'(?P<metadata>\{.*?\})'
}
pattern_strs = [
    r'queryId:"%(id)s",operationName:"%(name)s",operationType:".+?",metadata:%(meta)s\}\},?',
    r'params:\{id:"%(id)s",metadata:%(meta)s,name:"%(name)s",operationKind:".+?",text:',
    r'function [a-zA-Z$]{2}\(\)\{this.[a-z0-9_]{5}="%(id)s",this.[a-z0-9_]{5}="%(name)s"\}'
]
PATTERNS = [re.compile(s % PATTERN_MAPPING) for s in pattern_strs]


class GQLEndpointDict(TypedDict):
    queryId: str
    operationName: str
    metadata: NotRequired[dict]


def validate_endpoint(endpoint) -> bool:
    if not isinstance(endpoint, dict):
        return False
    if set(endpoint) - {'queryId', 'operationName', 'metadata'}:
        return False
    if not isinstance(endpoint.get('queryId'), str):
        return False
    if not isinstance(endpoint.get('operationName'), str):
        return False
    return True


def js_file_extract_endpoints(
    js: str,
    required_names: set[str] | None = None,
    missing_endpoint_handler: Callable[[str], GQLEndpointDict] | None = None
) -> list[GQLEndpointDict]:
    """
    Extracts endpoints in js with required_names
    """
    results = []
    seen = set()
    for pattern in PATTERNS:
        for m in pattern.finditer(js):
            endpoint_dict: GQLEndpointDict = m.groupdict()
            if not validate_endpoint(endpoint_dict):
                logger.info(f'Invalid endpoint: {endpoint_dict}')
                continue

            name = endpoint_dict['operationName']
            if required_names:
                if name not in required_names:
                    continue
                if name in seen:
                    continue

            metadata = endpoint_dict.get('metadata')
            if metadata:
                try:
                    endpoint_dict['metadata'] = chompjs.parse_js_object(metadata)
                except Exception as e:
                    logger.warning(f'Failed to parse metadata for "{name}": {e}')
                    continue

            if required_names:
                seen.add(name)

            results.append(endpoint_dict)
            logger.info(f'Extracted "{name}" (queryId={endpoint_dict["queryId"]})')

            if required_names and required_names == seen:
                return results

    if required_names:
        missings = required_names - seen
        if missings and not missing_endpoint_handler:
            raise ValueError(f'GraphQL endpoint {missings} not found and no missing_endpoint_handler provided.')
        for missing in missings:
            fallback = missing_endpoint_handler(missing)
            if not fallback:
                raise ValueError(f'GraphQL endpoint "{missing}" not found.')
            logger.warning(f'"GraphQL endpoint {missing}" not found in JS.')
            results.append(fallback)

    return results


async def _extract_endpoints(
    js_aiter: AsyncGenerator[tuple[str, str], None]
) -> tuple[list[GQLEndpointDict], dict[str, set[str]]]:
    """
    Used for building
    """
    results = []
    seen = set()
    js_endpoint_mapping = defaultdict(set)

    async for file_identifier, js in js_aiter:
        for endpoint in js_file_extract_endpoints(js):
            if not validate_endpoint(endpoint):
                logger.info(f'Invalid endpoint: {endpoint}')
                continue
            operation_name = endpoint['operationName']
            js_endpoint_mapping[operation_name].add(file_identifier)
            if operation_name not in seen:
                results.append(endpoint)
                seen.add(operation_name)
    return results, js_endpoint_mapping
