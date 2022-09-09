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

It's possible to customize the collection name of a model by specifying the `collection`
option in the `Config` class.

!!! example "Custom collection name example"
    ```python hl_lines="7-8"
    from odmantic import Model

    class CapitalCity(Model):
        name: str
        population: int

        class Config:
            collection = "city"
    ```
    Now, when `CapitalCity` instances will be persisted to the database, they will
    belong in the `city` collection instead of `capital_city`.

!!! warning
    Models and Embedded models inheritance is not supported yet.

### Indexes

#### Index definition

There are two ways to create indexes on a model in ODMantic. The first one is to use the
Field descriptors as explained in [Indexed fields](fields.md#indexed-fields) or
[Unique fields](fields.md#unique-fields). However, this way doesn't allow a great
flexibility on index definition.

That's why you can also use the `Config.indexes` generator to specify advanced indexes
(compound indexes, custom names). This static function defined in the `Config` class
should yield [odmantic.Index][odmantic.index.Index].


For example:

```python hl_lines="5 8 11-19" linenums="1"
--8<-- "modeling/compound_index.py"
```

This snippet creates 4 indexes on the `Product` model:

- An index on the `name` field defined with
  [the field descriptor](fields.md#indexed-fields), improving lookup performance by
  product name.

- A unique index on the `sku` field defined with
  [the field descriptor](fields.md#unique-fields), enforcing uniqueness of the `sku`
  field.

- A compound index on the `name` and `stock` fields, making sure the following query
  will be efficient (i.e. avoid a full collection scan):

    ```python
    engine.find(Product, Product.name == "banana", Product.stock > 5)
    ```

- A unique index on the `name` and `category` fields, making sure each category has
  unique product name.

!!! Tip "Sort orders with index definition"
    You can also specify the sort order of the fields in the index definition using
    [query.asc][odmantic.query.asc] and [query.desc][odmantic.query.desc] as presented
    in the [Sorting](querying.md#sorting) section.

    For example defining the following index on the `Event` model:
    ```python linenums="1" hl_lines="11-14"
    --8<-- "modeling/compound_index_sort_order.py"
    ```

    Will greatly improve the performance of the query:
    ```python
    engine.find(Event, sort=(asc(Event.name), desc(Event.date))
    ```
#### Index creation

In order to create and enable the indexes in the database, you need to call the
`engine.configure_database` method
(either [AIOEngine.configure_database][odmantic.engine.AIOEngine.configure_database] or
[SyncEngine.configure_database][odmantic.engine.SyncEngine.configure_database]).

{{ async_sync_snippet("modeling", "index_creation.py", hl_lines="6") }}

This method can also take a `#!python update_existing_indexes=True` parameter to update existing
indexes when the index definition changes. If not enabled, an exception will be thrown
when a conflicting index update happens.

#### Advanced indexes

In some cases, you might need a greater flexibility on the index definition (Geo2D,
Hashed, Text indexes for example), the
`Config.indexes` generator can also yield [pymongo.IndexModel](https://pymongo.readthedocs.io/en/stable/api/pymongo/operations.html?highlight=indexmodel#pymongo.operations.IndexModel){:target=blank_}
objects.

For example, defining a [text index](https://www.mongodb.com/docs/manual/core/index-text/){:target=blank_} :

```python hl_lines="11-15" linenums="1"
--8<-- "modeling/custom_text_index.py"
```


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

### Advanced Configuration

The model configuration is done in the same way as with Pydantic models: using a [Config
class](https://pydantic-docs.helpmanual.io/usage/model_config/){:target=blank_} defined
in the model body.

**Available options**:

 `#!python collection: str`
 :    Customize the collection name associated to the model. See [this
      section](modeling.md#collection) for more details about default collection naming.

 `#!python parse_doc_with_default_factories: bool`
 :    Wether to allow populating field values with default factories while parsing
      documents from the database. See
      [Advanced parsing behavior](raw_query_usage.md#advanced-parsing-behavior) for more
      details.

      Default: `#!python False`

`#!python indexes: Callable[[],Iterable[Union[Index, pymongo.IndexModel]]]`
 :    Define additional indexes for the model. See [Indexes](modeling.md#indexes) for
      more details.

      Default: `#!python lambda: []`

 `#!python title: str` *(inherited from Pydantic)*
 :    Title inferred in the JSON schema.

      Default: name of the model class

`#!python schema_extra: dict` *(inherited from Pydantic)*
 :    A dict used to extend/update the generated JSON Schema, or a callable to
      post-process it. See [Pydantic: Schema customization](https://pydantic-docs.helpmanual.io/usage/schema/#schema-customization){:target=_blank} for more details.

      Default: `#!python {}`

 `#!python anystr_strip_whitespace: bool` *(inherited from Pydantic)*
 :    Whether to strip leading and trailing whitespaces for str & byte types.

      Default: `#!python False`

`#!python json_encoders: dict` *(inherited from Pydantic)*
:    Customize the way types used in the model are encoded to JSON.

    ??? example "`json_encoders` example"

        For example, in order to serialize `datetime` fields as timestamp values:

        ```python
        class Event(Model):
            date: datetime

            class Config:
                json_encoders = {
                    datetime: lambda v: v.timestamp()
                }
        ```

`#!python extra: pydantic.Extra` *(inherited from Pydantic)*
 :    Whether to ignore, allow, or forbid extra attributes during model initialization. Accepts the string values of 'ignore', 'allow', or 'forbid', or values of the Extra enum. 'forbid' will cause validation to fail if extra attributes are included, 'ignore' will silently ignore any extra attributes, and 'allow' will assign the attributes to the model, reflecting them in the saved database documents and fetched instances.

      Default: `#!python Extra.ignore`

 `#!python json_loads` *(inherited from Pydantic)*
 :    Function used to decode JSON data

      Default: `#!python json.loads`

 `#!python json_dumps` *(inherited from Pydantic)*
 :    Function used to encode JSON data

      Default: `#!python json.dumps`




For more details and examples about the options inherited from Pydantic, you can have a
look to [Pydantic: Model
Config](https://pydantic-docs.helpmanual.io/usage/model_config/){:target=blank_}

!!! warning
    Only the options described above are supported and other options from Pydantic can't
    be used with ODMantic.

    If you feel the need to have an additional option inherited from Pydantic, you can
    [open an issue](https://github.com/art049/odmantic/issues/new){:target=blank}.

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
--8<-- "modeling/one_to_one.py"
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
    --8<-- "modeling/one_to_one_1.py"
    ```

    For more details, see the [Querying](querying.md) section.

### One to Many
Here, we will model the relation between a customer of an online shop and his shipping
addresses. A single customer can have multiple addresses but these addresses belong only
to the customer's account. He should be allowed to modify them without modifying others
addresses (for example if two family members use the same address, their addresses
should not be linked together).

```python hl_lines="6 15 20-33" linenums="1"
--8<-- "modeling/one_to_many.py"
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
    (`$all`, `$elemMatch`, `$size`). See the [Raw query usage](raw_query_usage.md) section for
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
--8<-- "modeling/many_to_one.py"
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

```python hl_lines="15 18-19 22 25 29" linenums="1"
--8<-- "modeling/many_to_many.py"
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
    --8<-- "modeling/many_to_many_1.py"
    ```
