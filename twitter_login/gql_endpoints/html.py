import json
import re

import chompjs
from bs4 import BeautifulSoup

INITIAL_STATE_PATTERN = re.compile(r'window.__INITIAL_STATE__')
SCRIPTS_LOADED_PATTERN = re.compile(r'window.__SCRIPTS_LOADED__')
JSON_PATTERN = re.compile(r'window\.__INITIAL_STATE__\s*=\s*({.*?});')
MAINJS_URL_PATTERN = re.compile(r'src="(https://[^"]*/)(main\.[a-f0-9]{7}a\.js)"')
# JS_HASH_MAPPING_PATTERN = re.compile(r'"\."\+(\{.+?\})\[\w\]\+"a\.js"')
ID_TO_NAME_OBJECT_PATTERN = re.compile(r'e=>""\+\(\((\{.+?\})\)')
ID_TO_HASH_OBJECT_PATTERN = re.compile(r'"\."\+\((\{.+\})\)')


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

        # {346: "bundle.NotABot",
        #  652: "ondemand.countries-zh",
        #  666: "bundle.Delegate", ...}
        id_to_name_table_match = ID_TO_NAME_OBJECT_PATTERN.search(script_tag.text)
        # {346: "c79eb1b",
        #  652: "44a1037",
        #  666: "7bb1cc0", ...}
        id_to_hash_table_match = ID_TO_HASH_OBJECT_PATTERN.search(script_tag.text)

        if not id_to_name_table_match:
            raise ValueError('JavaScript id to name table not found in html.')
        if not id_to_hash_table_match:
            raise ValueError('JavaScript id to hash table not found in html.')

        try:
            id_to_name_table = chompjs.parse_js_object(
                id_to_name_table_match.group(1)
            )
            id_to_hash_table = chompjs.parse_js_object(
                id_to_hash_table_match.group(1)
            )
        except Exception as e:
            raise ValueError('Failed to parse JS file object.') from e

        # make name:hash dict
        hash_mapping = {
            name: id_to_hash_table[i]
            for i, name in id_to_name_table.items()
        }
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
