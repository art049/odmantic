from abc import ABCMeta
from typing import TYPE_CHECKING, Type, TypeVar

from pydantic.error_wrappers import ValidationError

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


class DocumentParsingError(ValidationError):
    """Unable to parse the document

    Args:
        ValidationError ([type]): [description]
    """

    def __init__(self, validation_error: ValidationError):
        super().__init__(
            errors=validation_error.raw_errors, model=validation_error.model
        )
