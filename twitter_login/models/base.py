from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import dataclass_transform
else:
    def dataclass_transform(*args, **kwargs):
        return lambda x: x


@dataclass_transform(
    kw_only_default=True,
    slots_default=True
)
def model(*, reprs = None):
    if isinstance(reprs, str):
        reprs = (reprs,)

    def deco(cls):
        dtcls = dataclass(repr=False, slots=True, kw_only=True)(cls)

        if reprs:
            def repr(self):
                fields = [f'{r}="{getattr(self, r)}"' for r in reprs if hasattr(self, r)]
                return f'<{self.__class__.__name__} {", ".join(fields)}>'

            dtcls.__repr__ = repr

        return dtcls
    return deco
