from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..http import HTTPClient


class GQL:
    def __init__(self, http: HTTPClient) -> None:
        self.http = http