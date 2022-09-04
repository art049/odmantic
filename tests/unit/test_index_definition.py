from odmantic.field import Field
from odmantic.index import Index, ODMCompoundIndex, ODMSingleFieldIndex
from odmantic.model import EmbeddedModel, Model
from odmantic.query import asc, desc


def test_single_index_definition():
    class M(Model):
        f: int = Field(index=True)

    indexes = M.__indexes__()
    assert len(indexes) == 1
    index = indexes[0]
    assert isinstance(index, ODMSingleFieldIndex)
    assert not index.unique
    assert index.key_name == "f"


def test_single_index_with_key_name_definition():
    class M(Model):
        f: int = Field(key_name="custom", index=True)

    indexes = M.__indexes__()
    assert len(indexes) == 1
    index = indexes[0]
    assert isinstance(index, ODMSingleFieldIndex)
    assert not index.unique
    assert index.key_name == "custom"


def test_single_index_unique_definition():
    class M(Model):
        f: int = Field(unique=True)

    indexes = M.__indexes__()
    assert len(indexes) == 1
    index = indexes[0]
    assert isinstance(index, ODMSingleFieldIndex)
    assert index.unique


def test_single_index_index_and_unique_definition():
    class M(Model):
        f: int = Field(index=True, unique=True)

    indexes = M.__indexes__()
    assert len(indexes) == 1
    index = indexes[0]
    assert isinstance(index, ODMSingleFieldIndex)
    assert index.unique


def test_single_index_definition_from_generator():
    class M(Model):
        f: int

        class Config:
            @staticmethod
            def indexes():
                yield Index(M.f, unique=True)

    indexes = M.__indexes__()
    assert len(indexes) == 1
    index = indexes[0]
    assert isinstance(index, ODMSingleFieldIndex)
    assert index.unique


def test_compound_index_definition():
    class M(Model):
        f: int
        g: str

        class Config:
            @staticmethod
            def indexes():
                yield Index(M.f, desc(M.g), unique=True)

    indexes = M.__indexes__()
    assert len(indexes) == 1
    index = indexes[0]
    assert isinstance(index, ODMCompoundIndex)
    assert index.fields == (asc(M.f), desc(M.g))
    assert index.unique


def test_multiple_indexes_definition():
    class M(Model):
        f: int
        g: str
        h: float = Field(index=True)

        class Config:
            @staticmethod
            def indexes():
                yield Index(M.f, desc(M.g), unique=True, name="asc_desc")
                yield Index(M.g)

    indexes = M.__indexes__()
    assert len(indexes) == 3

    assert isinstance(indexes[0], ODMSingleFieldIndex)
    assert indexes[0].key_name == "h"

    assert isinstance(indexes[1], ODMCompoundIndex)
    assert indexes[1].fields == (asc(M.f), desc(M.g))
    assert indexes[1].unique
    assert indexes[1].index_name == "asc_desc"
    assert indexes[1].unique

    assert isinstance(indexes[2], ODMSingleFieldIndex)
    assert not indexes[2].unique


def test_embedded_index_definition():
    class E(EmbeddedModel):
        f: int

    class M(Model):
        e: E = Field(index=True)

    indexes = M.__indexes__()
    assert len(indexes) == 1
    index = indexes[0]

    assert isinstance(index, ODMSingleFieldIndex)
    assert index.key_name == "e"


def test_embedded_index_definition_generator():
    class E(EmbeddedModel):
        f: int

    class M(Model):
        e: E

        class Config:
            @staticmethod
            def indexes():
                yield Index(M.e)

    indexes = M.__indexes__()
    assert len(indexes) == 1
    index = indexes[0]

    assert isinstance(index, ODMSingleFieldIndex)
    assert index.key_name == "e"


def test_embedded_field_index_definition():
    class E(EmbeddedModel):
        f: int

    class M(Model):
        e: E

        class Config:
            @staticmethod
            def indexes():
                yield Index(M.e.f)

    indexes = M.__indexes__()
    assert len(indexes) == 1
    index = indexes[0]

    assert isinstance(index, ODMSingleFieldIndex)
    assert index.key_name == "e.f"
