from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Client


class BaseModel(ABC):
    _client: object

    def __init_subclass__(cls, **kwargs):
        reprs = kwargs.pop('reprs', None)
        super().__init_subclass__(**kwargs)
        if reprs:
            if isinstance(reprs, str):
                reprs = (reprs,)
            cls._reprs = reprs

    @classmethod
    @abstractmethod
    def _from_payload(cls, client: Client, payload: dict):
        ...

    def __repr__(self) -> str:
        reprs = self._reprs
        if not reprs:
            return super().__repr__()
        fields = [f'{r}="{getattr(self, r)}"' for r in reprs if hasattr(self, r)]
        return f'<{self.__class__.__name__} {", ".join(fields)}>'


def optional_subobject(cls, payload, field_name):
    data = payload.get(field_name)
    if data is None:
        return
    return cls(**data)
