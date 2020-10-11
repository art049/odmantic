# Modeling

## Models

To create a Model, simply inherit from the [Model][odmantic.model.Model] class and then
specify the field types and eventually their descriptors.

### Collection

Each Model will be linked to its own collection. By default, the collection name will be
created from the chosen class name and converted to
[snake_case](https://en.wikipedia.org/wiki/Snake_case). For example a model class named
`CapitalCity` will be stored in the collection named `capital_city`.

If the class name ends with `Model`, ODMantic will remove it to create the collection
name. For example, a model class named `PersonModel` will belong in the `person`
collection.

It's possible to change the collection name of a model by specifying the `__collection__`
class variable in the class body.

!!! example "Custom collection name example"
    ```python
    from odmantic import Model

    class CapitalCity(Model):
        __collection__ = "city"
        name: str
        population: int
    ```
    Now, when `CapitalCity` instances will be persisted to the database, they will
    belong in the `city` collection instead of `capital_city`.

!!! warning
    Models and Embedded models inheritance is not supported yet.

### Custom model validators

Exactly as done with pydantic, it's possible to define custom model validators as
described in the [pydantic: Root
Validators](https://pydantic-docs.helpmanual.io/usage/validators/#root-validators){:target=blank_}
documentation (this apply as well to Embedded Models).

In the following example, we will define a rectangle class and add two validators: The
first one will check that the height is greater than the width. The second one will
ensure that the area of the rectangle is less or equal to 9.

```python hl_lines="9 14-15 18-19 22-23 26-27 35 40-41 45 50-51 55 60-61" linenums="1"
--8<-- "modeling/custom_validators.py"
```

!!! tip
    You can define class variables in the Models using the `typing.ClassVar` type
    construct, as done in this example with `MAX_AREA`. Those class variables will be
    completely ignored by ODMantic while persisting instances to the database.

## Embedded Models

Using an embedded model will store it directly in the root model it's integrated
in. On the MongoDB side, the collection will contain the root documents and in inside
each of them, the embedded models will be directly stored.

Embedded models are especially useful while building
[one-to-one](https://en.wikipedia.org/wiki/One-to-one_(data_model)){:target=_blank} or
[one-to-many](https://en.wikipedia.org/wiki/One-to-many_(data_model)){:target=_blank}
relationships.

<!-- prettier-ignore -->
!!! note
    Since Embedded Models are directly embedded in the MongoDB collection of the root
    model, it will not be possible to query on them directly without specifying a root
    document.

The creation of an Embedded model is done by inheriting the
[EmbeddedModel][odmantic.model.EmbeddedModel] class. You can then define fields exactly
as for the regular Models.

### One to One

In this example, we will model the relation between a country and its capital city.
Since one capital city can belong to one and only one country, we can model this
relation as a One-to-One relationship. We will use an Embedded Model in this case.

```python hl_lines="4 12 19 24" linenums="1"
--8<-- "modeling/01.py"
```

Defining this relation is done in the same way as defining a new field. Here, the
`CapitalCity` class will be considered as a field type during the model definition.

The [Field][odmantic.field.Field] descriptor can be used as well for Embedded
Models in order to bring more flexibility (default values, Mongo key name, ...).

???+abstract "Content of the `country` collection after execution"
    ```json hl_lines="5-8 14-17"
    {
      "_id": ObjectId("5f79d7e8b305f24ca43593e2"),
      "name": "Sweden",
      "currency": "Swedish krona",
      "capital_city": {
        "name": "Stockholm",
        "population": 975904
      }
    }
    {
      "_id": ObjectId("5f79d7e8b305f24ca43593e1"),
      "name": "Switzerland",
      "currency": "Swiss franc",
      "capital_city": {
        "name": "Bern",
        "population": 1035000
      }
    }
    ```

<!-- prettier-ignore -->
!!! tip
    It is possible as well to define query filters based on embedded documents content.

    ```python hl_lines="2"
    --8<-- "modeling/01_1.py"
    ```

    For more details, see the [Filtering](filtering.md) section.

### One to Many
Here, we will model the relation between a customer of an online shop and his shipping
addresses. A single customer can have multiple addresses but these addresses belong only
to the customer's account. He should be allowed to modify them without modifying others
addresses (for example if two family members use the same address, their addresses
should not be linked together).

```python hl_lines="6 15 20-33" linenums="1"
--8<-- "modeling/02.py"
```

As done previously for the One to One relation, defining a One to Many relationship with
Embedded Models is done exactly as defining a field with its type being a sequence of
`Address` objects.

???+abstract "Content of the `customer` collection after execution"
    ```json hl_lines="4-17"
    {
      "_id": ObjectId("5f79eb116371e09b16e4fae4"),
      "name":"John Doe",
      "addresses":[
        {
          "street":"1757  Birch Street",
          "city":"Greenwood",
          "state":"Indiana",
          "zipcode":"46142"
        },
        {
          "street":"262  Barnes Avenue",
          "city":"Cincinnati",
          "state":"Ohio",
          "zipcode":"45216"
        }
      ]
    }
    ```

<!-- prettier-ignore -->
!!! tip
    To add conditions on the number of embedded elements, it's possible to use the
    `min_items` and `max_items` arguments of the [Field][odmantic.field.Field]
    descriptor. Another possibility is to use the `typing.Tuple` type.

<!-- prettier-ignore -->
!!! note
    Building query filters based on the content of a sequence of embedded documents is
    not supported yet (but this feature is planned for an upcoming release :fire:).

    Anyway, it's still possible to perform the filtering operation manually using Mongo
    [Array Operators](https://docs.mongodb.com/manual/reference/operator/query-array/){:target=_blank}
    (`$all`, `$elemMatch`, `$size`). See the [Usage outside the ODM](outside_odm.md) section for
    more details.

### Customization

Since the Embedded Models are considered as types by ODMantic, most of the complex type
constructs that could be imagined should be supported.

Some ideas which could be useful:

- Combine two different embedded models in a single field using `typing.Tuple`.

- Allow multiple Embedded model types using a `typing.Union` type.

- Make an Embedded model not required using `typing.Optional`.

- Embed the documents in a dictionary (using the `typing.Dict` type) to provide an
  additional key-value mapping to the embedded documents.

- Nest embedded documents

## Referenced models

Embedded models are really simple to use but sometimes it is needed as well to
have **many-to-one** (i.e. multiple entities referring to another single one) or
[many-to-many](https://en.wikipedia.org/wiki/Many-to-many_(data_model)){:target=_blank}
relationships. This is not really possible to model those using embedded documents and
in this case, references will come handy.
Another use case where references are useful is for one-to-one/one-to-many relations but
when the referenced model has to exist in its own collection, in order to be accessed on
 its own without any parent model specified.


### Many to One (Mapped)

In this part, we will model the relation between books and publishers. Let's consider that each
book has a single publisher. In this case, multiple books could be published by the same
publisher. We can thus model this relation as a many-to-one relationship.

```python hl_lines="4 10 13 19-23" linenums="1"
--8<-- "modeling/03.py"
```

The definition of a reference field **requires** the presence of the [Reference()][odmantic.reference.Reference]
descriptor. Once the models are defined, linking two instances is done simply by
assigning the reference field of referencing instance to the referenced instance.

??? question "Why is it required to include the Reference descriptor ?"
    The main goal behind enforcing the presence of the descriptor is to have a clear
    distinction between Embedded Models and References.

    In the future, a generic `Reference[T]` type will probably be included to make this
    distinction since it would make more sense than having to set a descriptor for each
    reference.

???+abstract "Content of the `publisher` collection after execution"
    ```json hl_lines="2 8"
    {
      "_id": ObjectId("5f7a0dc48a73b20f16e2a364"),
      "founded": 1826,
      "location": "FR",
      "name": "Hachette Livre"
    }
    {
      "_id": ObjectId("5f7a0dc48a73b20f16e2a365"),
      "founded": 1989,
      "location": "US",
      "name": "HarperCollins"
    }
    ```
    We can see that the publishers have been persisted to their collection even if no
    explicit save has been perfomed.
    When calling the [engine.save][odmantic.engine.AIOEngine.save] method, the engine
    will persist automatically the referenced documents.

    While fetching instances, the engine will as well resolve **every** reference.

???+abstract "Content of the `book` collection after execution"
    ```json hl_lines="4 10 16"
    {
      "_id": ObjectId("5f7a0dc48a73b20f16e2a366"),
      "pages": 304,
      "publisher": ObjectId("5f7a0dc48a73b20f16e2a364"),
      "title": "They Didn't See Us Coming"
    }
    {
      "_id": ObjectId("5f7a0dc48a73b20f16e2a367"),
      "pages": 256,
      "publisher": ObjectId("5f7a0dc48a73b20f16e2a364"),
      "title": "This Isn't Happening"
    }
    {
      "_id": ObjectId("5f7a0dc48a73b20f16e2a368"),
      "pages": 464,
      "publisher": ObjectId("5f7a0dc48a73b20f16e2a365"),
      "title": "Prodigal Summer"
    }
    ```
    The resulting books in the collection contain the publisher reference directly as a
    document attribute (using the reference name as the document's key).

<!-- prettier-ignore -->
!!! tip
    It's possible to customize the foreign key storage key using the `key_name` argument
    while building the [Reference][odmantic.reference.Reference] descriptor.

### Many to Many (Manual)
Here, we will model the relation between books and their authors. Since a book can have
multiple authors and an author can be authoring multiple books, we will model this
 relation as a many-to-many relationship.

!!! note
    Currently, ODMantic does not support mapped multi-references yet. But we will still
    define the relationship in a manual way.

```python hl_lines="14 18-19 22 25 29" linenums="1"
--8<-- "modeling/04.py"
```

We defined an `author_ids` field which holds the list of unique ids of the authors (This
`id` field in the `Author` model is generated implicitly by default).

Since this multi-reference is not mapped by the ODM, we have to persist the authors
manually.

???+abstract "Content of the `author` collection after execution"
    ```json hl_lines="2 6"
    {
      "_id": ObjectId("5f7a37dc7311be1362e1da4e"),
      "name": "David Beazley"
    }
    {
      "_id": ObjectId("5f7a37dc7311be1362e1da4f"),
      "name": "Brian K. Jones"
    }
    ```

???+abstract "Content of the `book` collection after execution"
    ```json hl_lines="5-8 14-16"
    {
      "_id": ObjectId("5f7a37dc7311be1362e1da50"),
      "title":"Python Cookbook"
      "pages":706,
      "author_ids":[
        ObjectId("5f7a37dc7311be1362e1da4e"),
        ObjectId("5f7a37dc7311be1362e1da4f")
      ],
    }
    {
      "_id": ObjectId("5f7a37dc7311be1362e1da51"),
      "title":"Python Essential Reference"
      "pages":717,
      "author_ids":[
        ObjectId("5f7a37dc7311be1362e1da4f")
      ],
    }
    ```

!!! example "Retrieving the authors of the Python Cookbook"
    First, it's required to fetch the ids of the authors. Then we can use the
    [in_][odmantic.query.in_] filter to select only the authors with the desired ids.
    ```python hl_lines="2" linenums="1"
    --8<-- "modeling/04_1.py"
    ```
