from ..gql_endpoints.endpoint import GQLState
from ..http import HTTPClient
from .gql import GQLClient
from .v11 import V11Client


class API:
    def __init__(self, http: HTTPClient, gql_state: GQLState) -> None:
        self.gql = GQLClient(http, gql_state)
        self.v11 = V11Client(http)
