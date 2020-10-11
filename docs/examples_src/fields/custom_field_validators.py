from typing import ClassVar

from pydantic import ValidationError, validator

from odmantic import Model


class SmallRectangle(Model):
    MAX_SIDE_SIZE: ClassVar[float] = 10

    length: float
    width: float

    @validator("width", "length")
    def check_small_sides(cls, v):
        if v > cls.MAX_SIDE_SIZE:
            raise ValueError(f"side is greater than {cls.MAX_SIDE_SIZE}")
        return v

    @validator("width")
    def check_width_length(cls, width, values, **kwargs):
        length = values.get("length")
        if length is not None and width > length:
            raise ValueError("width can't be greater than length")
        return width


print(SmallRectangle(length=2, width=1))
#> id=ObjectId('5f81e3c073103f509f97e374'), length=2.0, width=1.0

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
    width
      width can't be greater than length (type=value_error)
    """

try:
    SmallRectangle(length=40, width=3)
except ValidationError as e:
    print(e)
    """
    1 validation error for SmallRectangle
    length
      side is greater than 10 (type=value_error)
    """
