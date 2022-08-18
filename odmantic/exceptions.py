from abc import ABCMeta
from typing import TYPE_CHECKING, Any, List, Sequence, Type, TypeVar, Union

from pydantic.error_wrappers import ErrorWrapper, ValidationError

if TYPE_CHECKING:
    from odmantic.model import EmbeddedModel, Model, _BaseODMModel

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


ErrorList = List[Union[Sequence[Any], ErrorWrapper]]


class KeyNotFoundInDocumentError(ValueError):
    def __init__(self, key_name: str):
        super().__init__("key not found in document")
        self.key_name = f"'{key_name}'"


class ReferencedDocumentNotFoundError(ValueError):
    def __init__(self, key_name: str):
        super().__init__("referenced document not found")
        self.foreign_key_name = f"'{key_name}'"


class DocumentParsingError(ValidationError):
    """Unable to parse the document into an instance.

    Inherits from the `ValidationError` defined by Pydantic.

    Attributes:
      model (Union[Type[Model],Type[EmbeddedModel]]): model which could not be
        instanciated
    """

    def __init__(
        self,
        errors: Sequence[ErrorList],
        model: Type["_BaseODMModel"],
        primary_value: Any,
    ):
        super().__init__(errors, model)
        self.model: Union[Type["Model"], Type["EmbeddedModel"]]
        self.primary_value = primary_value

    def __str__(self) -> str:
        from odmantic import Model

        if issubclass(self.model, Model):
            return (
                f"{super().__str__()}\n"
                f"({self.model.__name__} instance details:"
                f" {self.model.__primary_field__}={repr(self.primary_value)})"
            )
        return super().__str__()
