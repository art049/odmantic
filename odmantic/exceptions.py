from abc import ABCMeta
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import pymongo
from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError

if TYPE_CHECKING:
    from odmantic.model import Model

ModelType = TypeVar("ModelType")


class BaseEngineException(Exception, metaclass=ABCMeta):
    """Base Exception raised by the engine while operating with the database."""

    def __init__(self, message: str, model: Type["Model"]):
        self.model: Type["Model"] = model
        super().__init__(message)


class DocumentNotFoundError(BaseEngineException):
    """The targetted document has not been found by the engine.

    Attributes:
      instance: the instance that has not been found
    """

    def __init__(self, instance: "Model"):
        self.instance: "Model" = instance
        super().__init__(
            f"Document not found for : {type(instance).__name__}. "
            f"Instance: {self.instance}",
            type(instance),
        )


class DuplicateKeyError(BaseEngineException):
    """The targetted document is duplicated according to a unique index.

    Attributes:
      instance: the instance that has not been found
      driver_error: the original driver error
    """

    def __init__(
        self, instance: "Model", driver_error: pymongo.errors.DuplicateKeyError
    ):
        self.instance: "Model" = instance
        self.driver_error = driver_error
        super().__init__(
            f"Duplicate key error for: {type(instance).__name__}. "
            f"Instance: {self.instance} "
            f"Driver error: {self.driver_error}",
            type(instance),
        )


ErrorList = List[InitErrorDetails]


def ODManticCustomError(
    error_type: str,
    message_template: str,
    context: Union[Dict[str, Any], None] = None,
) -> PydanticCustomError:
    odm_error_type = f"odmantic::{error_type}"
    return PydanticCustomError(odm_error_type, message_template, context)


class _KeyNotFoundInDocumentError(ValueError):
    def __init__(self, key_name: str):
        super().__init__("key not found in document")
        self.key_name = f"'{key_name}'"


def KeyNotFoundInDocumentError(key_name: str) -> PydanticCustomError:
    return ODManticCustomError(
        "key_not_found_in_document",
        "Key '{key_name}' not found in document",
        {"key_name": key_name},
    )


class _ReferencedDocumentNotFoundError(ValueError):
    def __init__(self, key_name: str):
        super().__init__("referenced document not found")
        self.foreign_key_name = f"'{key_name}'"


def ReferencedDocumentNotFoundError(foreign_key_name: str) -> PydanticCustomError:
    return ODManticCustomError(
        "referenced_document_not_found",
        "Referenced document not found for foreign key '{foreign_key_name}'",
        {"foreign_key_name": foreign_key_name},
    )


class _IncorrectGenericEmbeddedModelValue(ValueError):
    def __init__(self, value: Any):
        super().__init__("incorrect generic embedded model value")
        self.value = value


def IncorrectGenericEmbeddedModelValue(value: Any) -> PydanticCustomError:
    return ODManticCustomError(
        "incorrect_generic_embedded_model_value",
        "Incorrect generic embedded model value '{value}'",
        {"value": value},
    )


def DocumentParsingError(errors: ErrorList) -> ValidationError:
    """Unable to parse the document into an instance.

    Inherits from the `ValidationError` defined by Pydantic.

    Attributes:
      model (Union[Type[Model],Type[EmbeddedModel]]): model which could not be
        instanciated
    """
    return ValidationError.from_exception_data(
        title="Document parsing error",
        line_errors=errors,
    )
