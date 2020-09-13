from tests.zoo.book_embedded import Book, Publisher


def test_embedded_eq():
    pub = Publisher(name="O'Reilly Media", founded=1980, location="CA")
    assert (Book.publisher == pub) == {
        "publisher": {
            "$eq": {"name": "O'Reilly Media", "founded": 1980, "location": "CA"}
        }
    }


def test_embedded_eq_on_subfield():
    assert (Book.publisher.location == "EU") == {"publisher.location": {"$eq": "EU"}}
