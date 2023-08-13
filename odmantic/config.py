from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, cast

import pymongo
from pydantic.config import ConfigDict

if TYPE_CHECKING:
    import odmantic.index as ODMIndex


class ODMConfigDict(ConfigDict, total=False):
    collection: str | None
    parse_doc_with_default_factories: bool
    indexes: Callable[[], Iterable[ODMIndex.Index | pymongo.IndexModel]] | None


PYDANTIC_CONFIG_OPTIONS = set(ConfigDict.__annotations__.keys())
PYDANTIC_ALLOWED_CONFIG_OPTIONS = {
    "title",
    "json_schema_extra",
    "str_strip_whitespace",
    "arbitrary_types_allowed",
    "extra",
}
PYDANTIC_FORBIDDEN_CONFIG_OPTIONS = (
    PYDANTIC_ALLOWED_CONFIG_OPTIONS - PYDANTIC_ALLOWED_CONFIG_OPTIONS
)
ODM_CONFIG_OPTIONS = set(ODMConfigDict.__annotations__.keys()) - PYDANTIC_CONFIG_OPTIONS
ODM_CONFIG_ALLOWED_CONFIG_OPTIONS = ODM_CONFIG_OPTIONS | PYDANTIC_ALLOWED_CONFIG_OPTIONS


EnforcedPydanticConfig = ConfigDict(validate_default=True, validate_assignment=True)


def validate_config(config: ODMConfigDict, cls_name: str) -> ODMConfigDict:
    """Validate the model configuration, enforcing some Pydantic options and making sure
    only compatible options are used.
    """
    out_config: Dict[str, Any] = {
        "title": None,
        "json_schema_extra": None,
        "str_strip_whitespace": False,
        "arbitrary_types_allowed": False,
        "extra": None,
        **EnforcedPydanticConfig,
        "collection": None,
        "parse_doc_with_default_factories": False,
        "indexes": None,
    }

    for config_key, value in config.items():
        if config_key in ODM_CONFIG_ALLOWED_CONFIG_OPTIONS:
            out_config[config_key] = value
        elif config_key in PYDANTIC_FORBIDDEN_CONFIG_OPTIONS:
            raise ValueError(
                f"'{cls_name}': configuration attribute '{config_key}'"
                " from Pydantic is not supported"
            )
        else:
            raise ValueError(
                f"'{cls_name}': unknown configuration attribute '{config_key}'"
            )
    return cast(ODMConfigDict, out_config)
