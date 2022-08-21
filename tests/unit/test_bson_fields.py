import re
from datetime import datetime
from decimal import Decimal
from typing import Pattern

import pytest
import pytz
from bson.decimal128 import Decimal128
from bson.objectid import ObjectId
from bson.regex import Regex
from pydantic.error_wrappers import ValidationError

from odmantic.field import Field
from odmantic.model import Model

pytestmark = pytest.mark.asyncio


def test_datetime_non_naive():
    class ModelWithDate(Model):
        field: datetime

    with pytest.raises(ValueError):
        ModelWithDate(field=datetime.now(tz=pytz.timezone("Europe/Amsterdam")))

    with pytest.raises(ValueError):
        ModelWithDate(field="2018-11-02T23:59:01.824+10:00")


def test_datetime_non_naive_utc():
    class ModelWithDate(Model):
        field: datetime = Field(datetime.now(tz=pytz.utc))

    ModelWithDate()


def test_datetime_non_naive_utc_as_simplified_extended_iso_format_string():
    class ModelWithDate(Model):
        field: datetime = Field("2018-11-02T23:59:01.824Z")

    ModelWithDate()


def test_datetime_non_naive_utc_as_gmt_zero_offset_string():
    class ModelWithDate(Model):
        field: datetime = Field("2018-11-02T23:59:01.824+00:00")

    ModelWithDate()


def test_datetime_naive():
    class ModelWithDate(Model):
        field: datetime = Field(default_factory=datetime.utcnow)

    ModelWithDate()


def test_datetime_milliseconds_rounding():
    class ModelWithDate(Model):
        field: datetime

    sample_datetime = datetime.now()
    sample_datetime = sample_datetime.replace(
        microsecond=10001
    )  # Ensure we have some micro seconds that will be truncated
    inst = ModelWithDate(field=sample_datetime)

    assert inst.field.microsecond != sample_datetime.microsecond
    assert inst.field == sample_datetime.replace(microsecond=10000)

    sample_datetime = sample_datetime.replace(microsecond=999501)
    inst = ModelWithDate(field=sample_datetime)

    assert inst.field == sample_datetime.replace(microsecond=999000)


def test_validate_datetime_from_strings():
    class ModelWithDate(Model):
        field: datetime

    sample_datetime = datetime.now().replace(
        microsecond=10000
    )  # Ensure we have no micro seconds that will be truncated
    sample_datetime_str = str(sample_datetime)
    inst = ModelWithDate(field=sample_datetime_str)
    assert inst.field == sample_datetime


def test_validate_bson_objectid():
    class MyModel(Model):
        pass

    my_oid = ObjectId()
    instance = MyModel(id=str(my_oid))
    assert instance.id == my_oid


def test_validate_invalid_bson_objectid():
    class MyModel(Model):
        pass

    with pytest.raises(ValidationError) as exc_info:
        MyModel(id="not an objectid")
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("id",)
    assert "invalid ObjectId specified" in errors[0]["msg"]


def test_validate_decimal_valid_string():
    class MyModel(Model):
        field: Decimal

    value = "3.152345596"
    instance = MyModel(field=value)
    assert isinstance(instance.field, Decimal)
    assert str(instance.field) == value


def test_validate_decimal_valid_bson_decimal():
    class MyModel(Model):
        field: Decimal

    str_value = "3.152345596"
    value = Decimal128(str_value)
    instance = MyModel(field=value)
    assert isinstance(instance.field, Decimal)
    assert str(instance.field) == str_value


def test_validate_decimal_invalid_string():
    class MyModel(Model):
        field: Decimal

    with pytest.raises(ValidationError) as exc_info:
        MyModel(field="3abcd.15")
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("field",)
    assert "value is not a valid decimal" in errors[0]["msg"]


def test_validate_bson_decimal_valid_string():
    class MyModel(Model):
        field: Decimal128

    value = "3.152345596"
    instance = MyModel(field=value)
    assert isinstance(instance.field, Decimal128)
    assert str(instance.field) == value


def test_validate_bson_decimal_valid_bson_decimal():
    class MyModel(Model):
        field: Decimal128

    value = Decimal128("3.152345596")
    instance = MyModel(field=value)
    assert isinstance(instance.field, Decimal128)
    assert instance.field == value


def test_validate_bson_decimal_invalid_string():
    class MyModel(Model):
        field: Decimal128

    with pytest.raises(ValidationError) as exc_info:
        MyModel(field="3abcd.15")
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("field",)
    assert "value is not a valid decimal" in errors[0]["msg"]


def test_validate_regex_valid_regex():
    class MyModel(Model):
        field: Regex

    regex = Regex("^.*$")
    instance = MyModel(field=regex)
    assert isinstance(instance.field, Regex)
    assert instance.field == regex


def test_validate_regex_valid_string():
    class MyModel(Model):
        field: Regex

    value = "^.*$"
    instance = MyModel(field=value)
    assert isinstance(instance.field, Regex)
    assert instance.field.pattern == value


def test_validate_regex_invalid_string():
    class MyModel(Model):
        field: Regex

    with pytest.raises(ValidationError) as exc_info:
        MyModel(field="^((")
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("field",)
    assert "Invalid regular expression" in errors[0]["msg"]


def test_validate_pattern_valid_string():
    class MyModel(Model):
        field: Pattern

    value = "^.*$"
    instance = MyModel(field=value)
    assert isinstance(instance.field, Pattern)
    assert instance.field.pattern == value


def test_validate_pattern_valid_bson_regex():
    class MyModel(Model):
        field: Pattern

    value = Regex("^.*$", flags="im")
    flags_int_value = re.compile("", flags=re.I | re.M).flags
    instance = MyModel(field=value)
    assert isinstance(instance.field, Pattern)
    assert instance.field.pattern == value.pattern
    assert instance.field.flags == flags_int_value


def test_validate_pattern_invalid_string():
    class MyModel(Model):
        field: Pattern

    with pytest.raises(ValidationError) as exc_info:
        MyModel(field="^((")
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("field",)
    assert "Invalid regular expression" in errors[0]["msg"]
