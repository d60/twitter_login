from dataclasses import dataclass, field
from logging import getLogger
from typing import Any, Callable, Generic, Protocol, Type, TypeVar

model_logger = getLogger(__name__ + '._model')

M = TypeVar('M', bound='ModelProtocol')
O = TypeVar('O', bound='LazyMixin')


@dataclass(repr=False, slots=True)
class LazyMixin:
    _lazy_sources: dict = field(default_factory=dict, init=False)
    _lazy_cache: dict = field(default_factory=dict, init=False)


class ModelProtocol(Protocol):
    @classmethod
    def _from_payload(cls: Type[M], payload: dict, **kwargs) -> M: ...


class Lazy(Generic[M, O]):
    def __init__(
        self,
        type: Type[M],
        kwargs_factory: Callable[[O], dict[str, Any]] = None
    ) -> None:
        self.type = type
        self.kwargs_factory = kwargs_factory

    def __set_name__(self, owner: Type[O], name):
        self.name = name

    def __set__(self, obj: O, value: dict | list | None | M):
        if value is None:
            return

        if self.name in obj._lazy_cache:
            raise RuntimeError(f'{self.name} already materialized.')

        if isinstance(value, self.type):
            # Accept setting instance of the expected class directly
            model_logger.info(f'Set value directly for: {self.name}')
            obj._lazy_cache[self.name] = value
            return

        if self.name in obj._lazy_sources:
            raise RuntimeError(f'Source for {self.name} already exists.')

        if not isinstance(value, (dict, list)):
            raise TypeError('Source must be a dict or list.')

        model_logger.info(f'Set source value for {self.name}')
        obj._lazy_sources[self.name] = value

    def __get__(self, obj: O | None, owner: Type[O]):
        if obj is None:
            return self

        if self.name in obj._lazy_cache:
            # return cached value
            model_logger.info(f'Return cached value for: {self.name}')
            return obj._lazy_cache[self.name]

        source = obj._lazy_sources.pop(self.name, None)
        if source is None:
            return

        # prepare _from_payload kwargs
        if self.kwargs_factory:
            kwargs = self.kwargs_factory(obj)
        else:
            kwargs = {}

        if isinstance(source, dict):
            value = self.type._from_payload(source, **kwargs)
        elif isinstance(source, list):
            value = [
                self.type._from_payload(payload, **kwargs)
                for payload in source
            ]
        else:
            raise TypeError('Source must be a dict or list.')

        # cache value
        model_logger.info(f'Generated and cached value for: {self.name}')
        obj._lazy_cache[self.name] = value
        return value
