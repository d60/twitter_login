from ..gql_endpoints.endpoint import GQLState
from ..http import HTTPClient
from .gql import GQL
from .v11 import V11


class API:
    def __init__(self, http: HTTPClient, gql_state: GQLState) -> None:
        self.gql = GQL(http, gql_state)
        self.v11 = V11(http)
