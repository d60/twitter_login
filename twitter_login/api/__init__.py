from ..http import HTTPClient
from .gql import GQL
from .v11 import V11


class API:
    def __init__(self, http: HTTPClient) -> None:
        self.http = http
        self.gql = GQL(http)
        self.v11 = V11(http)
