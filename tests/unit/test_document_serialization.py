from decimal import Decimal

import bson

from odmantic import Model


def test_objectid_serialization():
    class M(Model): ...

    instance = M()
    doc = instance.model_dump_doc()
    assert isinstance(doc["_id"], bson.ObjectId)
    assert doc["_id"] == instance.id


def test_extra_allowed_bson_serialization():
    class M(Model):
        ...

        model_config = {"extra": "allow"}

    instance = M(extra_field=Decimal("1.1"))
    doc = instance.model_dump_doc()
    assert isinstance(doc["extra_field"], bson.Decimal128)
