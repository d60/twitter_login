import json
from logging import getLogger
from pathlib import Path

from .extract_endpoint import validate_endpoint

logger = getLogger(__name__)
default_dir = Path(__file__).parent.parent.resolve() / '.cache'


def load_json(path: Path, validator):
    if not path.exists():
        return None
    try:
        with path.open(encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.warning(f'Failed to load cache from "{path}": {e}')
        return

    v = validator(data)
    if v:
        logger.warning(f'Invalid cache: {v}')
        return
    logger.info(f'Loaded cache from {path}')
    return data

def dump_json(path: Path, obj, validator):
    v = validator(obj)
    if v:
        logger.warning(f'Invalid cache: {v}')
        return
    try:
        with path.open('w', encoding='utf-8') as f:
            json.dump(obj, f)
    except Exception as e:
        logger.warning(f'Failed to cache data to "{path}": {e}')
        return
    logger.info(f'Cached data to {path}')


def validate_hash_mapping(data):
    if not isinstance(data, dict):
        return f'Invalid data type "{data.__class__.__name__}"'
    for k, v in data.items():
        if not isinstance(k, str):
            return f'Invalid hash key "{k}"'
        if not isinstance(v, str) or len(v) != 7:
            return f'Invalid hash value "{v}"'


def validate_endpoints(data):
    if not isinstance(data, list):
        return f'Invalid data type "{data.__class__.__name__}"'
    for e in data:
        if not validate_endpoint(e):
            return 'Endpoint must be dict and have "queryId" and "operationName"'


def validate_feature_switches(data):
    if not isinstance(data, dict):
        return f'Invalid data type "{data.__class__.__name__}"'
    for k, v in data.items():
        if not isinstance(k, str):
            return f'Invalid feature switch key "{k}"'
        if not isinstance(v, bool):
            return f'Invalid feature switch value "{v}"'


class GQLCache:
    def __init__(self, cache_dir: str | Path | None = None) -> None:
        if cache_dir is None:
            cache_dir = default_dir
        if isinstance(cache_dir, str):
            cache_dir = Path(cache_dir)
        self.dir = cache_dir

    def make_cache_dir(self):
        if not self.dir.exists():
            self.dir.mkdir(parents=True)

    @property
    def hash_path(self):
        return self.dir / 'hash_mapping.json'

    @property
    def endpoints_path(self):
        return self.dir / 'endpoints.json'

    @property
    def feature_switches_path(self):
        return self.dir / 'feature_switches.json'

    def get_cached_hash_mapping(self):
        return load_json(self.hash_path, validate_hash_mapping)

    def get_cached_endpoints(self):
        return load_json(self.endpoints_path, validate_endpoints)

    def get_cached_feature_switches(self):
        return load_json(self.feature_switches_path, validate_feature_switches)

    def cache_hash_mapping(self, obj):
        self.make_cache_dir()
        dump_json(self.hash_path, obj, validate_hash_mapping)

    def cache_endpoints(self, obj):
        self.make_cache_dir()
        dump_json(self.endpoints_path, obj, validate_endpoints)

    def cache_feature_switches(self, obj):
        self.make_cache_dir()
        dump_json(self.feature_switches_path, obj, validate_feature_switches)

