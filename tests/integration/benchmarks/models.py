"""Models based on https://github.com/tortoise/orm-benchmarks"""

from datetime import datetime, timezone
from decimal import Decimal
from random import choice
from typing import Iterator, Optional

from typing_extensions import Literal, get_args

from odmantic import Field, Model

Level = Literal[10, 20, 30, 40, 50]
VALID_LEVELS = list(get_args(Level))


def utc_now():
    return datetime.now(timezone.utc)


class SmallJournal(Model):
    timestamp: datetime = Field(default_factory=utc_now)
    level: Level = Field(index=True)
    text: str = Field(index=True)

    @classmethod
    def get_random_instances(cls, context: str, count: int) -> Iterator["SmallJournal"]:
        for i in range(count):
            yield cls(level=choice(VALID_LEVELS), text=f"From {context}, item {i}")


class JournalWithRelations(Model):
    timestamp: datetime = Field(default_factory=utc_now)
    level: Level = Field(index=True)
    text: str = Field(index=True)

    # parent


class BigJournal(Model):
    timestamp: datetime = Field(default_factory=utc_now)
    level: Level = Field(index=True)
    text: str = Field(index=True)

    col_float1: float = Field(default=2.2)
    col_smallint1: int = Field(default=2)
    col_int1: int = Field(default=2000000)
    col_bigint1: int = Field(default=99999999)
    col_char1: str = Field(default=255, max_length=255)
    col_text1: str = Field(
        default="Moo,Foo,Baa,Waa,Moo,Foo,Baa,Waa,Moo,Foo,Baa,Waa",
    )
    col_decimal1: Decimal = Field(default=Decimal("2.2"))
    col_json1: dict = Field(
        default={"a": 1, "b": "b", "c": [2], "d": {"e": 3}, "f": True},
    )

    col_float2: Optional[float] = Field(default=None)
    col_smallint2: Optional[int] = Field(default=None)
    col_int2: Optional[int] = Field(default=None)
    col_bigint2: Optional[int] = Field(default=None)
    col_char2: Optional[str] = Field(default=None, max_length=255)
    col_text2: Optional[str] = Field(
        default=None,
    )
    col_decimal2: Optional[Decimal] = Field(default=None)
    col_json2: Optional[dict] = Field(
        default=None,
    )
