from typing import List

from odmantic import Field, Model


class ExampleModel(Model):
    small_int: int = Field(le=10)
    big_int: int = Field(gt=1000)
    even_int: int = Field(multiple_of=2)

    small_float: float = Field(lt=10)
    big_float: float = Field(ge=1e10)

    short_string: str = Field(max_length=10)
    long_string: str = Field(min_length=100)
    string_starting_with_the: str = Field(regex=r"^The")

    short_str_list: List[str] = Field(max_items=5)
    long_str_list: List[str] = Field(min_items=15)
