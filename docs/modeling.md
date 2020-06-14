# Modeling

## Relations ?

## Embedded Models

### One to One relationships

```python hl_lines="1 9"
class Publisher(EmbeddedModel):
    name: str
    founded: int
    location: str

class Book(Model):
    title: str
    pages: int
    publisher: Publisher

book = Book(
    title="MongoDB: The Definitive Guide",
    pages=216,
    publisher=Publisher(name="O'Reilly Media", founded=1980, location="CA"),
)

await engine.add(book)
```

<!-- prettier-ignore -->
!!! tip
    It is possible to build a define query filters on embedded documents
    ``` python hl_lines="1"
    book_from_CA = await engine.find_one(Book, Book.publisher.location == "CA")
    print(book_from_CA)
    #> Book(title="MongoDB: The Definitive Guide", pages=216, publisher=Publisher, name="O'Reilly Media", founded=1980, location="CA"))
    ```

### One to Many relationships

```python hl_lines="1 10"
class Address(EmbeddedModel):
    street: str
    city: str
    state: str
    zip: str


class Patron(Model):
    name: str
    addresses: List[Address]
```

<!-- prettier-ignore -->
!!! note
    To add conditions on the number of embedded elements, it's possible to pass extra arguments during the Embedded Field definition (TODO).
    Another possibility is to use the `typing.Tuple` type.

## Referenced Models

```python hl_lines="9"
class Publisher(Model):
    name: str
    founded: int
    location: str

class Book(Model):
    title: str
    pages: int
    publisher: Publisher = Reference()
```
