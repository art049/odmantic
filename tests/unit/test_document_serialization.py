import bson

from odmantic import Model


def test_objectid_serialization():
    class M(Model):
        ...

    instance = M()
    doc = instance.doc()
    assert isinstance(doc["_id"], bson.ObjectId)
    assert doc["_id"] == instance.id
