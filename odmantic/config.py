from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Tuple,
    TypedDict,
    Union,
    cast,
)

import pymongo
from pydantic import ConfigDict
from pydantic.config import ExtraValues, JsonSchemaExtraCallable

from odmantic.utils import is_dunder

if TYPE_CHECKING:
    import odmantic.index as ODMIndex


class _ODManticConfigDict(TypedDict, total=False):
    """Configuration fields specific to odmantic"""

    collection: str | None
    parse_doc_with_default_factories: bool
    indexes: Callable[[], Iterable[Union[ODMIndex.Index, pymongo.IndexModel]]] | None


class _InheritedConfigDict(TypedDict, total=False):
    """Allowed configuration inherited from pydantic"""

    title: str | None
    json_schema_extra: dict[str, object] | JsonSchemaExtraCallable | None
    str_strip_whitespace: bool
    arbitrary_types_allowed: bool
    extra: ExtraValues | None


ODM_ALLOWED_CONFIG_OPTIONS = {
    name for name in dir(_ODManticConfigDict) if not is_dunder(name)
}

PYD_ALLOWED_CONFIG_OPTIONS = {
    name for name in dir(_InheritedConfigDict) if not is_dunder(name)
}

PYD_FORBIDDEN_CONFIG_OPTIONS = {
    name for name in dir(ConfigDict) if not is_dunder(name)
} - PYD_ALLOWED_CONFIG_OPTIONS


class ODMConfigDict(_ODManticConfigDict, _InheritedConfigDict):
    pass


EnforcedPydanticConfig = ConfigDict(validate_default=True, validate_assignment=True)


def validate_config(config: ODMConfigDict, cls_name: str) -> ODMConfigDict:
    """Validate the model configuration"""
    pydantic_config: Dict[str, Any] = {
        "title": None,
        "json_schema_extra": None,
        "str_strip_whitespace": False,
        "arbitrary_types_allowed": False,
        "extra": None,
        **EnforcedPydanticConfig,
    }
    odmantic_config: Dict[str, Any] = {
        "collection": None,
        "parse_doc_with_default_factories": False,
        "indexes": None,
    }
    for config_key, value in config.items():
        if config_key in ODM_ALLOWED_CONFIG_OPTIONS:
            odmantic_config[config_key] = value
        elif config_key in PYD_ALLOWED_CONFIG_OPTIONS:
            pydantic_config[config_key] = value
        elif config_key in PYD_FORBIDDEN_CONFIG_OPTIONS:
            raise ValueError(
                f"'{cls_name}': configuration attribute '{config_key}'"
                " from Pydantic is not supported"
            )
        else:
            raise ValueError(
                f"'{cls_name}': unknown configuration attribute '{config_key}'"
            )
    return cast(ODMConfigDict, {**pydantic_config, **odmantic_config})
