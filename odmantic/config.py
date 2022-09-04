from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional, Type, Union

import pymongo
from pydantic import Extra
from pydantic.main import BaseConfig
from pydantic.typing import AnyCallable

from odmantic.bson import BSON_TYPES_ENCODERS
from odmantic.utils import is_dunder

if TYPE_CHECKING:
    import odmantic.index as ODMIndex

try:
    from pydantic.config import SchemaExtraCallable
except ModuleNotFoundError:  # pragma: no cover
    # pydantic<1.9.0
    # Cannot use type: ignore for all versions
    # -> https://github.com/python/mypy/issues/8823
    from pydantic.main import SchemaExtraCallable  # type: ignore


class BaseODMConfig:
    """Base class of the Config defined in the Models
    Defines as well the fields allowed to be passed.
    """

    collection: Optional[str] = None
    parse_doc_with_default_factories: bool = False

    @staticmethod
    def indexes() -> Iterable[Union[ODMIndex.Index, pymongo.IndexModel]]:
        return []

    # Inherited from pydantic
    title: Optional[str] = None
    json_encoders: Dict[Type[Any], AnyCallable] = {}
    schema_extra: Union[Dict[str, Any], "SchemaExtraCallable"] = {}
    anystr_strip_whitespace: bool = False
    json_loads: Callable[[str], Any] = json.loads
    json_dumps: Callable[..., str] = json.dumps
    arbitrary_types_allowed: bool = False
    extra: Extra = Extra.ignore


ALLOWED_CONFIG_OPTIONS = {name for name in dir(BaseODMConfig) if not is_dunder(name)}


class EnforcedPydanticConfig:
    """Configuration options enforced to work with Models"""

    validate_all = True
    validate_assignment = True


def validate_config(
    cls_config: Type[BaseODMConfig], cls_name: str
) -> Type[BaseODMConfig]:
    """Validate and build the model configuration"""
    for name in dir(cls_config):
        if not is_dunder(name) and name not in ALLOWED_CONFIG_OPTIONS:
            raise ValueError(f"'{cls_name}': 'Config.{name}' is not supported")

    if cls_config is BaseODMConfig:
        bases = (EnforcedPydanticConfig, BaseODMConfig, BaseConfig)
    else:
        bases = (
            EnforcedPydanticConfig,
            cls_config,
            BaseODMConfig,
            BaseConfig,
        )  # type:ignore

    # Merge json_encoders to preserve bson type encoders
    namespace = {
        "json_encoders": {
            **BSON_TYPES_ENCODERS,
            **getattr(cls_config, "json_encoders", {}),
        }
    }
    return type("Config", bases, namespace)
