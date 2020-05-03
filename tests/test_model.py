from odmantic.model import Model


class TheClassName(Model):
    ...


class TheClassNameModel(Model):
    ...


class TheClassNameOverriden(Model):
    __collection__ = "collection_name"


def test_auto_collection_name():

    assert TheClassName.__collection__ == "the_class_name"

    assert TheClassNameModel.__collection__ == "the_class_name"

    assert TheClassNameOverriden.__collection__ == "collection_name"


def test_auto_collection_name_nested():
    class theNestedClassName(Model):
        ...

    assert theNestedClassName.__collection__ == "the_nested_class_name"

    class TheNestedClassNameOverriden(Model):
        __collection__ = "collection_name"

    assert TheNestedClassNameOverriden.__collection__ == "collection_name"
