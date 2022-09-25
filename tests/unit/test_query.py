from typing import List

from odmantic.model import Model
from odmantic.query import QueryExpression, SortExpression, any_, asc, eq, gte
from tests.zoo.book_embedded import Book, Publisher
from tests.zoo.tree import TreeKind, TreeModel


def test_embedded_eq():
    pub = Publisher(name="O'Reilly Media", founded=1980, location="CA")
    assert (Book.publisher == pub) == {
        "publisher": {
            "$eq": {"name": "O'Reilly Media", "founded": 1980, "location": "CA"}
        }
    }


def test_embedded_eq_on_subfield():
    assert (Book.publisher.location == "EU") == {"publisher.location": {"$eq": "EU"}}


def test_eq_on_enum():
    assert (TreeModel.kind == TreeKind.BIG) == {"kind": {"$eq": TreeKind.BIG.value}}
    assert (TreeModel.kind == "big") == {"kind": {"$eq": "big"}}


def test_query_repr():
    assert (
        repr(TreeModel.name == "Spruce")
        == "QueryExpression({'name': {'$eq': 'Spruce'}})"
    )


def test_query_empty_repr():
    assert repr(QueryExpression()) == "QueryExpression()"


def test_sort_repr():
    assert repr(asc(TreeModel.name)) == "SortExpression({'name': 1})"


def test_sort_empty_repr():
    assert repr(SortExpression()) == "SortExpression()"


class ModelWithIntArray(Model):
    array: List[int]


def test_array_any_eq():
    expected = {"array": {"$elemMatch": {"$eq": 42}}}
    assert any_(ModelWithIntArray.array, {"$eq": 42}) == expected
    assert eq(any_(ModelWithIntArray.array), 42) == expected
    # assert ModelWithIntArray.array.any().eq(42) == expected
    # assert (ModelWithIntArray.array.any() == 42) == expected


def test_array_any_gte():
    expected = {"array": {"$elemMatch": {"$gte": 42}}}
    assert any_(ModelWithIntArray.array, {"$gte": 42}) == expected
    # assert ModelWithIntArray.array.any().gte(42) == expected
    # assert (ModelWithIntArray.array.any() >= 42) == expected


# def test_array_all_eq():
#     expected = {"array": {"$all": {"$eq": 42}}}
#     assert eq(ModelWithIntArray.array.all(), 42) == expected
#     assert ModelWithIntArray.array.all().eq(42) == expected
#     assert (ModelWithIntArray.array.all() == 42) == expected


# def test_array_all_gte():
#     expected = {"array": {"$all": {"$gte": 42}}}
#     assert ModelWithIntArray.array.all().gte(42) == expected
#     assert gte(ModelWithIntArray.array.all(), 42) == expected
#     assert (ModelWithIntArray.array.all() >= 42) == expected
