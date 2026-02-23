import json
import re

import chompjs
from bs4 import BeautifulSoup

INITIAL_STATE_PATTERN = re.compile(r'window.__INITIAL_STATE__')
SCRIPTS_LOADED_PATTERN = re.compile(r'window.__SCRIPTS_LOADED__')
JSON_PATTERN = re.compile(r'window\.__INITIAL_STATE__\s*=\s*({.*?});')
JS_HASH_MAPPING_PATTERN = re.compile(r'"\."\+(\{.+?\})\[\w\]\+"a\.js"')
MAINJS_URL_PATTERN = re.compile(r'src="(https://[^"]*/)(main\.[a-f0-9]{7}a\.js)"')


class HTMLExtractor:
    """Class for extracting data from html."""

    def __init__(self, html) -> None:
        self.html = html
        self.soup = BeautifulSoup(html, 'html.parser')

    def extract_initial_state(self):
        script_tag = self.soup.find('script', string=INITIAL_STATE_PATTERN)
        if not script_tag:
            raise ValueError('__INITIAL_STATE__ not found in html.')
        match = JSON_PATTERN.search(script_tag.text)
        if not match:
            raise ValueError('__INITIAL_STATE__ not found in html.')
        initial_state_json = match.group(1)
        try:
            initial_state = json.loads(initial_state_json)
        except json.JSONDecodeError as e:
            raise ValueError('Failed to decode initial state JSON.') from e
        return initial_state

    def extract_js_hash_mapping(self) -> dict[str, str]:
        script_tag = self.soup.find('script', string=SCRIPTS_LOADED_PATTERN)
        if not script_tag:
            raise ValueError('script tag not found in html.')
        match = JS_HASH_MAPPING_PATTERN.search(script_tag.text)
        if not match:
            raise ValueError('JS files object not found in html.')
        raw_obj = match.group(1)
        try:
            hash_mapping = chompjs.parse_js_object(raw_obj)
        except Exception as e:
            raise ValueError('Failed to parse JS file object.') from e
        return hash_mapping

    def extract_path_and_mainjs(self):
        """
        Returns js path and main.js filename
        ('https://abs.twimg.com/responsive-web/client-web/', 'main.xxxxxxxa.js')
        """
        match = MAINJS_URL_PATTERN.search(self.html)
        if not match:
            raise ValueError('JS URL not found in html.')
        groups = match.groups()
        if len(groups) < 2:
            raise ValueError('Failed to extract JS URL.')
        return groups
