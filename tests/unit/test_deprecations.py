import pytest

from odmantic import EmbeddedModel, Model


class M(Model): ...


def test_deprecated_copy():
    with pytest.deprecated_call():
        M().copy()


def test_deprecated_update():
    with pytest.deprecated_call():
        M().update({})


def test_deprecated_update_basemodel():
    # EmbeddedModel is a subclass of BaseModel not redefine update
    class E(EmbeddedModel): ...

    with pytest.deprecated_call():
        E().update({})


def test_deprecated_doc():
    with pytest.deprecated_call():
        M().doc()


def test_deprecated_parse_doc():
    with pytest.deprecated_call():
        M().parse_doc(
            {
                "_id": "5f8352a87a733b8b18b0cb27",
            }
        )
