import asyncio
from logging import getLogger
from typing import AsyncGenerator

from ..http import HTTPClient
from ..utils import optional_chaining
from .cache import GQLCache
from .data import BUILDTIME_DEFAULT_FEATURE_SWITCHES, BUILDTIME_ENDPOINTS, BUILDTIME_HASH_MAPPING, REQUIRED_ENDPOINTS_MAPPING
from .endpoint import GQLState
from .extract_endpoint import js_file_extract_endpoints
from .html import HTMLExtractor

logger = getLogger(__name__)


class GQLEndpointsManager:
    def __init__(self, http: HTTPClient) -> None:
        """
        required_endpoints_mapping : {'filename1': ['OperationName1', 'OperationName2', ...], ...}
        hash_mapping        : {'filename1': 'abcd1234', 'filename2': 'efgh5678'}
        """
        self.http = http
        self.required_endpoints_mapping = REQUIRED_ENDPOINTS_MAPPING
        self.initial_state: dict | None = None
        self.js_hash_mapping: dict | None = None
        self.js_url_path: str | None = None
        self.state = GQLState()
        self.cache = GQLCache()
        self.load_cached_or_buildtime_data()

    def load_cached_or_buildtime_data(self):
        """Loads cached data or build-time data if no cache is exists."""
        self.state.hash_mapping = self.cache.get_cached_hash_mapping() or BUILDTIME_HASH_MAPPING
        self.state.update_endpoints(self.cache.get_cached_endpoints() or BUILDTIME_ENDPOINTS)
        self.state.update_feature_switches(
            self.cache.get_cached_feature_switches() or BUILDTIME_DEFAULT_FEATURE_SWITCHES
        )

    async def load_html(self):
        headers = self.http.build_headers(authorization=False, csrf_token=False)
        response = await self.http.get('https://x.com/home', headers=headers)
        html = response.text
        self.extract_html(html)
        logger.info('Data extracted and updated from html.')

    def extract_html(self, html):
        html_extractor = HTMLExtractor(html)
        self.initial_state = html_extractor.extract_initial_state()
        self.js_hash_mapping = html_extractor.extract_js_hash_mapping()
        self.js_url_path, main_js_filename = html_extractor.extract_path_and_mainjs()
        parts = main_js_filename.split('.')
        if len(parts) != 3:
            raise ValueError(f'Wrong JS file name: {main_js_filename}')
        self.js_hash_mapping[parts[0]] = parts[1].removesuffix('a')

    def get_update_required_files(self) -> list[tuple[str, str]]:
        """
        Return files whose hashes differ from the current hashes.
        tuples of filename and newhash
        """
        filenames = self.required_endpoints_mapping.keys()
        files_data = []
        for filename in filenames:
            old_hash = self.state.hash_mapping.get(filename)
            new_hash = self.js_hash_mapping.get(filename)
            if not new_hash:
                raise ValueError(f'File hash for "{filename}" not found.')
            if old_hash == new_hash:
                continue
            files_data.append((filename, new_hash))
        return files_data

    def build_file_url(self, filename, hash):
        return f'{self.js_url_path}{filename}.{hash}a.js'

    async def update_required_js_aiter(self) -> AsyncGenerator[tuple[str, str], None]:
        """
        Yields filename and jsfile content.
        """
        sem = asyncio.Semaphore(10)
        async def fetch_file(filename, hash):
            url = self.build_file_url(filename, hash)
            async with sem:
                response = await self.http.get(url)
                return filename, response.text
        files_data = self.get_update_required_files()
        tasks = [asyncio.create_task(fetch_file(f, h)) for f, h in files_data]
        for i in asyncio.as_completed(tasks):
            yield await i

    def handle_missing_endpoint(self, name):
        current_endpoint = self.state.endpoints.get(name)
        if current_endpoint:
            logger.info(f'"{name}" not found. Using current data instead.')
            return current_endpoint.as_dict()
        buildtime_endpoint = next(
            filter(
                lambda x: x.get('operationName') == name,
                BUILDTIME_ENDPOINTS
            ),
            None
        )
        if buildtime_endpoint:
            logger.info(f'"{name}" not found. Using build time data instead.')
            return buildtime_endpoint

    async def fetch_updated_endpoints(self):
        results = []
        async for filename, js in self.update_required_js_aiter():
            results += js_file_extract_endpoints(
                js, set(self.required_endpoints_mapping[filename]), self.handle_missing_endpoint
            )
            logger.info(f'Updated {len(results)} from {filename}')
        return results

    async def update_endpoints(self):
        """
        Returns updated endpoints.
        """
        updated_endpoints = await self.fetch_updated_endpoints()
        if not updated_endpoints:
            logger.info('No endpoints updated.')
            return []
        hash_mapping = {
            filename: self.js_hash_mapping[filename]
            for filename in self.required_endpoints_mapping.keys()
        }
        self.state.hash_mapping = hash_mapping
        self.state.update_endpoints(updated_endpoints)
        logger.info(f'{len(updated_endpoints)} endpoints were updated.')
        return updated_endpoints

    async def update_state(self):
        await self.load_html()
        results = await self.update_endpoints()
        feature_switches = self.get_feature_switches()
        if feature_switches:
            self.state.update_feature_switches(feature_switches)
        if results:
            self.cache_data()

    def cache_data(self):
        hash_mapping = self.state.hash_mapping
        endpoints = [e.as_dict() for e in self.state.endpoints.values()]
        feature_switches = self.state.feature_switches
        if hash_mapping:
            self.cache.cache_hash_mapping(hash_mapping)
        if endpoints:
            self.cache.cache_endpoints(endpoints)
        if feature_switches:
            self.cache.cache_feature_switches(feature_switches)

    def get_feature_switches(self):
        initial_state = self.initial_state
        if initial_state is None:
            return
        conf = (optional_chaining(initial_state, 'featureSwitch', 'user', 'config')
                or optional_chaining(initial_state, 'featureSwitch', 'defaultConfig'))
        if conf is None:
            return
        return {
            k: v['value'] for k, v in conf.items()
            if 'value' in v and isinstance(v['value'], bool)
        }
