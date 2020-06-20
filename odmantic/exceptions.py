from typing import TypeVar

from odmantic.model import Model

ModelType = TypeVar("ModelType")


class DuplicatePrimaryKeyError(Exception):
    def __init__(self, duplicated_intance: Model):
        self.model = type(duplicated_intance)
        self.duplicated_instance = duplicated_intance
        self.duplicated_field = self.model.__primary_key__
        self.duplicated_value = getattr(duplicated_intance, self.duplicated_field)
        super().__init__(
            f"Duplicate primary key error model: {self.model.__name__} primary_key:"
            f"{self.duplicated_field} duplicated_value: {self.duplicated_value}"
        )
