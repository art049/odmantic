import re
from types import FunctionType
from typing import Dict, Optional, TypeVar, no_type_check

import pydantic

from .exceptions import MultiplePrimaryKeysException
from .fields import MISSING_DEFAULT, Field
from .types import objectId

UNTOUCHED_TYPES = FunctionType, property, type, classmethod, staticmethod


def is_valid_odm_field(name: str) -> bool:
    return not name.startswith("__") and not name.endswith("__")


def to_snake_case(s: str) -> str:
    tmp = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", tmp).lower()


class ModelMetaclass(pydantic.main.ModelMetaclass):
    @no_type_check  # noqa C901
    def __new__(cls, name, bases, namespace, **kwargs):  # noqa C901
        if (namespace.get("__module__"), namespace.get("__qualname__")) != (
            "model",
            "Model",
        ):
            print(cls)
            print(name)
            print(bases)
            print(namespace)
            primary_key: Optional[str] = None
            odm_name_mapping: Dict[str, str] = {}
            annotations = namespace.get("__annotations__", {})
            for field_name in annotations:
                if not is_valid_odm_field(field_name):
                    continue
                field_cls_default = namespace.get(field_name)
                if isinstance(field_cls_default, Field):
                    if field_cls_default.primary_key:
                        if primary_key is not None:
                            # TODO handle inheritance with primary keys
                            raise MultiplePrimaryKeysException
                        primary_key = field_name
                        # TODO handle primary key + mongo_name

                    if field_cls_default.mongo_name is not None:
                        odm_name_mapping[field_name] = field_cls_default.mongo_name

                    if field_cls_default.default is not MISSING_DEFAULT:
                        namespace[field_name] = field_cls_default.default
                    else:
                        del namespace[field_name]
            # TODO handle auto primary key
            namespace["__primary_key__"] = primary_key
            namespace["__odm_name_mapping__"] = odm_name_mapping

            if "__collection__" not in namespace:
                cls_name = name
                if cls_name.endswith("Model"):
                    cls_name = cls_name[:-5]  # Strip Model in the class name
                namespace["__collection__"] = to_snake_case(cls_name)

        return super().__new__(cls, name, bases, namespace, **kwargs)


T = TypeVar("T", bound="Model")


class Model(pydantic.BaseModel, metaclass=ModelMetaclass):
    __collection__: str
    __primary_key__: str
    __odm_name_mapping__: Dict[str, str]

    id: Optional[objectId]

    def __init_subclass__(cls):
        for field in cls.__fields__.values():
            setattr(cls, field.name, Field(mongo_name=field.name))
        setattr(cls, "id", Field(primary_key=True, mongo_name="_id"))


class EmbeddedModel(pydantic.BaseModel):
    ...
