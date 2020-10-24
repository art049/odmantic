from odmantic.query import QueryExpression, SortExpression, asc
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
