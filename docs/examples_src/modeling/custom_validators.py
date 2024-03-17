from typing import ClassVar

from pydantic import ValidationError, model_validator

from odmantic import Model


class SmallRectangle(Model):
    MAX_AREA: ClassVar[float] = 9

    length: float
    width: float

    @model_validator(mode="before")
    def check_width_length(cls, values):
        length = values.get("length", 0)
        width = values.get("width", 0)
        if width > length:
            raise ValueError("width can't be greater than length")
        return values

    @model_validator(mode="before")
    def check_area(cls, values):
        length = values.get("length", 0)
        width = values.get("width", 0)
        if length * width > cls.MAX_AREA:
            raise ValueError(f"area is greater than {cls.MAX_AREA}")
        return values


print(SmallRectangle(length=2, width=1))
# > id=ObjectId('5f81e3c073103f509f97e374'), length=2.0, width=1.0

try:
    SmallRectangle(length=2)
except ValidationError as e:
    print(e)
    """
    1 validation error for SmallRectangle
    width
      field required (type=value_error.missing)
    """

try:
    SmallRectangle(length=2, width=3)
except ValidationError as e:
    print(e)
    """
    1 validation error for SmallRectangle
      Value error, width can't be greater than length
    """

try:
    SmallRectangle(length=4, width=3)
except ValidationError as e:
    print(e)
    """
    1 validation error for SmallRectangle
    __root__
      Value error, area is greater than 9
    """
