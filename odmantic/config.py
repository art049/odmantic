from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, cast

import pymongo
from pydantic.config import ConfigDict

if TYPE_CHECKING:
    import odmantic.index as ODMIndex


class ODMConfigDict(ConfigDict, total=False):
    collection: str | None
    """Customize the collection name associated to the model"""
    parse_doc_with_default_factories: bool
    """Wether to allow populating field values with default factories while parsing
    documents from the database"""
    indexes: Callable[[], Iterable[ODMIndex.Index | pymongo.IndexModel]] | None
    """Define additional indexes for the model"""


PYDANTIC_CONFIG_OPTIONS = set(ConfigDict.__annotations__.keys())
PYDANTIC_ALLOWED_CONFIG_OPTIONS = {
    "title",
    "json_schema_extra",
    "str_strip_whitespace",
    "arbitrary_types_allowed",
    "extra",
    "json_encoders",
}
PYDANTIC_FORBIDDEN_CONFIG_OPTIONS = (
    PYDANTIC_CONFIG_OPTIONS - PYDANTIC_ALLOWED_CONFIG_OPTIONS
)
ODM_CONFIG_OPTIONS = set(ODMConfigDict.__annotations__.keys()) - PYDANTIC_CONFIG_OPTIONS
ODM_CONFIG_ALLOWED_CONFIG_OPTIONS = ODM_CONFIG_OPTIONS | PYDANTIC_ALLOWED_CONFIG_OPTIONS


ENFORCED_PYDANTIC_CONFIG = ConfigDict(validate_default=True, validate_assignment=True)


def validate_config(config: ODMConfigDict, cls_name: str) -> ODMConfigDict:
    """Validate the model configuration, enforcing some Pydantic options"""
    out_config: Dict[str, Any] = {
        "title": None,
        "json_schema_extra": None,
        "str_strip_whitespace": False,
        "arbitrary_types_allowed": False,
        "extra": None,
        **ENFORCED_PYDANTIC_CONFIG,
        "collection": None,
        "parse_doc_with_default_factories": False,
        "indexes": None,
    }

    for config_key, value in config.items():
        if config_key in ENFORCED_PYDANTIC_CONFIG:
            raise ValueError(
                f"'{cls_name}': configuration attribute '{config_key}' is "
                f"enforced to {ENFORCED_PYDANTIC_CONFIG.get(config_key,'unknown')} "
                "by ODMantic and cannot be changed"
            )
        elif config_key in PYDANTIC_FORBIDDEN_CONFIG_OPTIONS:
            raise ValueError(
                f"'{cls_name}': configuration attribute '{config_key}'"
                " from Pydantic is not supported"
            )
        elif config_key in ODM_CONFIG_ALLOWED_CONFIG_OPTIONS:
            out_config[config_key] = value
        else:
            raise ValueError(
                f"'{cls_name}': unknown configuration attribute '{config_key}'"
            )
    return cast(ODMConfigDict, out_config)
