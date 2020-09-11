from datetime import datetime

import pytest
import pytz

from odmantic.model import Model

pytestmark = pytest.mark.asyncio


def test_datetime_non_naive():
    class ModelWithDate(Model):
        field: datetime

    with pytest.raises(ValueError):
        ModelWithDate(field=datetime.now(tz=pytz.utc))

    with pytest.raises(ValueError):
        ModelWithDate(field=datetime.now(tz=pytz.timezone("Europe/Amsterdam")))


def test_datetime_mili_rounding():
    class ModelWithDate(Model):
        field: datetime

    sample_datetime = datetime.now()
    sample_datetime = sample_datetime.replace(
        microsecond=10001
    )  # Ensure we have some micro seconds that will be truncated
    inst = ModelWithDate(field=sample_datetime)

    assert inst.field.microsecond != sample_datetime.microsecond
    assert inst.field == sample_datetime.replace(microsecond=10000)
