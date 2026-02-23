from dataclasses import dataclass
from logging import getLogger

from .extract_endpoint import GQLEndpointDict

logger = getLogger(__name__)


@dataclass
class Endpoint:
    operationName: str
    queryId: str
    feature_switches: dict[str, bool]
    metadata: dict | None = None

    @property
    def url(self) -> str:
        return f'https://x.com/i/api/graphql/{self.queryId}/{self.operationName}'

    @property
    def features(self) -> list[str] | None:
        if not self.metadata:
            return
        names = self.metadata.get('featureSwitches')
        if names is None:
            return
        return {
            name: self.feature_switches.get(name)
            for name in names
        }

    @property
    def field_toggles(self) -> list[str] | None:
        if self.metadata:
            return self.metadata.get('fieldToggles')

    def as_dict(self) -> GQLEndpointDict:
        dct: GQLEndpointDict = {
            'operationName': self.operationName,
            'queryId': self.queryId
        }
        if self.metadata is not None:
            dct['metadata'] = self.metadata
        return dct


class GQLState:
    def __init__(self) -> None:
        # these values will updated by GQLEndpointManager
        self.endpoints: dict[str, Endpoint] = {}
        self.feature_switches: dict[str, bool] = {}
        self.hash_mapping: dict[str, str] = {}

    def update_endpoints(self, endpoint_dicts: list[GQLEndpointDict]) -> None:
        for endpoint_dict in endpoint_dicts:
            self.endpoints[endpoint_dict['operationName']] = Endpoint(**endpoint_dict, feature_switches=self.feature_switches)

    def update_feature_switches(self, feature_switches_dict: dict):
        self.feature_switches.update(feature_switches_dict)
        # required = self.required_feature_switches()
        # for k, v in feature_switches_dict.items():
        #     if k in required:
        #         self.feature_switches[k] = v

    # def required_feature_switches(self):
    #     required_features = set()
    #     for endpoint in self.endpoints.values():
    #         features = endpoint.feature_switch_names
    #         if features:
    #             required_features |= set(features)
    #     return required_features

    def __repr__(self) -> str:
        return '<GQLState (' + ', '.join(
            f'{endpoint.queryId}/{name}' for name, endpoint in self.endpoints.items()
        ) + ')>'
