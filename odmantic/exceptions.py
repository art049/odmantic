from abc import ABCMeta
from typing import Type, TypeVar

from odmantic.model import Model

ModelType = TypeVar("ModelType")


class BaseEngineException(Exception, metaclass=ABCMeta):
    """Base Exception raised by the engine while operating on a model"""

    def __init__(self, message: str, model: Type[Model]):
        self.model: Type[Model] = model
        super().__init__(message)


class DuplicatePrimaryKeyError(BaseEngineException):
    def __init__(self, duplicated_instance: Model):
        self.duplicated_instance = duplicated_instance
        self.duplicated_field = self.model.__primary_key__
        self.duplicated_value = getattr(duplicated_instance, self.duplicated_field)
        super().__init__(
            f"Duplicate primary key error model: {self.model.__name__} primary_key:"
            f"{self.duplicated_field} duplicated_value: {self.duplicated_value}",
            type(duplicated_instance),
        )


class DocumentNotFoundError(BaseEngineException):
    """The targetted document has not been found by the engine

    Attributes:
      instance: the instance that has not been found
    """

    def __init__(self, instance: Model):
        self.instance: Model = instance
        super().__init__(
            f"Document not found for : {type(instance).__name__}. "
            f"Instance: {self.instance}",
            type(instance),
        )
