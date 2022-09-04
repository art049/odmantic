# Fields
## The `id` field

The [`ObjectId` data type](https://docs.mongodb.com/manual/reference/method/ObjectId/){:target=blank_}
 is the default primary key type used by MongoDB. An `ObjectId` comes with many
 information embedded into it (timestamp, machine identifier, ...). Since by default
 MongoDB will create a field `_id` containing an `ObjectId` primary key, ODMantic will
 bind it automatically to an implicit field named `id`.


```python hl_lines="9 10" linenums="1"
--8<-- "fields/objectid.py"
```

!!! info "ObjectId creation"
    This `id` field will be generated on instance creation, before saving the instance
    to the database. This helps to keep consistency between the instances persisted to
    the database and the ones only created locally.


Even if this behavior is convenient, it is still possible to [define custom primary
keys](#primary-key).


## Field types
### Optional fields

By default, every single field will be required. To specify a field as non-required, the
easiest way is to use the `typing.Optional` generic type that will allow the field to
take the `None` value as well (it will be stored as `null` in the database).

```python hl_lines="8" linenums="1"
--8<-- "fields/optional.py"
```

### Union fields

As explained in the [Python Typing
documentation](https://docs.python.org/3/library/typing.html#typing.Optional){:target=bank_},
`Optional[X]` is equivalent to `Union[X, None]`. That implies that the field type will
be either `X` or `None`.

It's possible to combine any kind of type using the `typîng.Union` type constructor. For
example if we want to allow both `string` and `int` in a field:

```python hl_lines="7" linenums="1"
--8<-- "fields/union.py"
```


!!! question "NoneType"
    Internally python describes the type of the `None` object as `NoneType` but in
    practice, `None` is used directly in type annotations ([more details](https://mypy.readthedocs.io/en/stable/kinds_of_types.html#optional-types-and-the-none-type){:target=bank_}).

### Enum fields

To define choices, it's possible to use the standard `enum` classes:

```python hl_lines="6-8 13" linenums="1"
--8<-- "fields/enum.py"
```

!!! abstract "Resulting documents in the collection `tree` after execution"
    ```json hl_lines="7"
    { "_id" : ObjectId("5f818f2dd5708527282c49b6"), "kind" : "big", "name" : "Sequoia" }
    { "_id" : ObjectId("5f818f2dd5708527282c49b7"), "kind" : "small", "name" : "Spruce" }
    ```

If you try to use a value not present in the allowed choices, a [ValidationError](https://pydantic-docs.helpmanual.io/usage/models/#error-handling){:target=blank_} exception will be raised.

!!! warning "Usage of `enum.auto`"
    If you might add some values to an `Enum`, it's strongly recommended not to use the
    `enum.auto` value generator. Depending on the order you add choices, it could
    completely break the consistency with documents stored in the database.

    ??? example "Unwanted behavior example"

        ```python hl_lines="11-12" linenums="1"
        --8<-- "fields/inconsistent_enum_1.py"
        ```

        ```python hl_lines="6 12-15" linenums="1"
        --8<-- "fields/inconsistent_enum_2.py"
        ```

### Container fields
#### List

```python linenums="1"
--8<-- "fields/container_list.py"
```

!!! tip
    It's possible to define element count constraints for a list field using the
    [Field][odmantic.field.Field] descriptor.

#### Tuple

```python linenums="1"
--8<-- "fields/container_tuple.py"
```

#### Dict

!!! tip
    For mapping types with already known keys, you can see the [embedded models
    section](modeling.md#embedded-models).

```python  linenums="1"
--8<-- "fields/container_dict.py"
```

!!! tip "Performance tip"
    Whenever possible, try to avoid mutable container types (`List`, `Set`, ...) and
    prefer their Immutable alternatives (`Tuple`, `FrozenSet`, ...). This will allow
    ODMantic to speedup database writes by only saving the modified container fields.

### `BSON` types integration

ODMantic supports native python BSON types ([`bson`
package](https://api.mongodb.com/python/current/api/bson/index.html){:target=blank_}).
Those types can be used directly as field types:

- [`bson.ObjectId`](https://api.mongodb.com/python/current/api/bson/objectid.html){:target=blank_}

- [`bson.Int64`](https://api.mongodb.com/python/current/api/bson/int64.html){:target=blank_}

- [`bson.Decimal128`](https://api.mongodb.com/python/current/api/bson/decimal128.html){:target=blank_}

- [`bson.Regex`](https://api.mongodb.com/python/current/api/bson/regex.html){:target=blank_}

- [`bson.Binary`](https://api.mongodb.com/python/current/api/bson/binary.html#bson.binary.Binary){:target=blank_}


??? info "Generic python to BSON type map"

    | Python type            | BSON type  | Comment                                                      |
    | ---------------------- | :--------: | ------------------------------------------------------------ |
    | `bson.ObjectId`        | `objectId` |
    | `bool`                 |   `bool`   |                                                              |
    | `int`                  |   `int`    | value between -2^31 and 2^31 - 1                             |
    | `int`                  |   `long`   | value not between -2^31 and 2^31 - 1                         |
    | `bson.Int64`           |   `long`   |
    | `float`                |  `double`  |
    | `bson.Decimal128`      | `decimal`  |                         |
    | `decimal.Decimal`      | `decimal`  |
    | `str`                  |  `string`  |
    | `typing.Pattern`       |  `regex`   |
    | `bson.Regex`           |  `regex`   |
    | `bytes`                | `binData`  |
    | `bson.Binary`          | `binData`  |
    | `datetime.datetime`    |   `date`   | microseconds are truncated, only naive datetimes are allowed |
    | `typing.Dict`          |  `object`  |
    | `typing.List`          |  `array`   |
    | `typing.Sequence`      |  `array`   |
    | `typing.Tuple[T, ...]` |  `array`   |

### Pydantic fields

Most of the types supported by pydantic are supported by ODMantic. See [pydantic:
Field Types](https://pydantic-docs.helpmanual.io/usage/types){:target=bank_} for more
field types.

Unsupported fields:

- `typing.Callable`

Fields with a specific behavior:

- `datetime.datetime`: Only [naive datetime
  objects](https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive){:target=blank_}
  will be allowed as MongoDB doesn't store the timezone information. Also, the
  microsecond information will be truncated.


## Customization

The field customization can mainly be performed using the [Field][odmantic.field.Field]
descriptor. This descriptor is here to define everything about the field except its
type.

### Default values

The easiest way to set a default value to a field is by assigning this default value
directly while defining the model.

```python hl_lines="6" linenums="1"
--8<-- "fields/default_value.py"
```

You can combine default values and an existing [Field][odmantic.field.Field]
descriptor using the `default` keyword argument.

``` python hl_lines="6" linenums="1"
--8<-- "fields/default_value_field.py"
```

!!! info "Default factory"
    You may as well define a factory function instead of a value using the
    `default_factory` argument of the [Field][odmantic.field.Field] descriptor.

    By default, the default factories won't be used while parsing MongoDB documents.
    It's possible to enable this behavior with the `parse_doc_with_default_factories`
    [Config](modeling.md#advanced-configuration) option.

!!! tip
    For `typing.Optional` fields, `None` is already set as the default value

!!! warning "Default values validation"
    Currently the default values are not validated yet during the model creation.

    An inconsistent default value might raise a
    [ValidationError](https://pydantic-docs.helpmanual.io/usage/models/#error-handling){:target=blank_}
    while building an instance.

### Document structure

By default, the MongoDB documents fields will be named after the field name. It is
possible to override this naming policy by using the `key_name` argument in the
[Field][odmantic.field.Field] descriptor.

{{ async_sync_snippet("fields", "custom_key_name.py", hl_lines="5") }}

!!! abstract "Resulting documents in the collection `player` after execution"

    ```json hl_lines="3"
    {
      "_id": ObjectId("5ed50fcad11d1975aa3d7a28"),
      "username": "Jack",
    }
    ```
    See [this section](#the-id-field) for more details about the `_id` field that has been added.



### Primary key

While ODMantic will by default populate the `id` field as a primary key, you can use any
other field as the primary key.

{{ async_sync_snippet("fields", "custom_primary_field.py", hl_lines="5") }}

!!! abstract "Resulting documents in the collection `player` after execution"
    ```json
    {
        "_id": "Leeroy Jenkins"
    }
    ```
!!! info
    The Mongo name of the primary field will be enforced to `_id` and you will not be
    able to change it.

!!! warning
    Using mutable types (Set, List, ...) as primary field might result in inconsistent
    behaviors.



### Indexed fields

You can define an index on a single field by using the `index` argument of the
[Field][odmantic.field.Field] descriptor.

More details about index creation can be found in the
[Indexes](modeling.md#indexes) section.

{{ async_sync_snippet("fields", "indexed_field.py", hl_lines="6 10") }}


!!! warning
    When using indexes, make sure to call the `configure_database` method
    ([AIOEngine.configure_database][odmantic.engine.AIOEngine.configure_database] or
    [SyncEngine.configure_database][odmantic.engine.SyncEngine.configure_database]) to
    persist the indexes to the database.


### Unique fields

In the same way, you can define unique constrains on a single field by using the
`unique` argument of the [Field][odmantic.field.Field] descriptor. This will ensure that
values of this fields are unique among all the instances saved in the database.

More details about unique index creation can be found in the
[Indexes](modeling.md#indexes) section.

{{ async_sync_snippet("fields", "unique_field.py", hl_lines="5 9 15-18") }}

!!! warning
    When using indexes, make sure to call the `configure_database` method
    ([AIOEngine.configure_database][odmantic.engine.AIOEngine.configure_database] or
    [SyncEngine.configure_database][odmantic.engine.SyncEngine.configure_database]) to
    persist the indexes to the database.


## Validation

As ODMantic strongly relies on pydantic when it comes to data validation, most of the
validation features provided by pydantic are available:

- Add field validation constraints by using the [Field descriptor][odmantic.field.Field]
  ```python linenums="1"
  --8<-- "fields/validation_field_descriptor.py"
  ```

- Use strict types to prevent to coercion from compatible types ([pydantic: Strict Types](https://pydantic-docs.helpmanual.io/usage/types/#strict-types){:target=blank_})
  ```python linenums="1"
  --8<-- "fields/validation_strict_types.py"
  ```

- Define custom field validators ([pydantic:
  Validators](https://pydantic-docs.helpmanual.io/usage/validators/){:target=blank_})
  ```python linenums="1"
  --8<-- "fields/custom_field_validators.py"
  ```

- Define custom model validators: [more details](modeling.md#custom-model-validators)

## Custom field types
Exactly in the same way pydantic allows it, it's possible to define custom field types as well with ODMantic ([pydantic: Custom data types](https://pydantic-docs.helpmanual.io/usage/types/#custom-data-types){:target=blank_}).

Sometimes, it might be required to customize as well the field BSON serialization. In
order to do this, the field class will have to implement the `__bson__` class method.

```python linenums="1" hl_lines="13-14 21-26"
--8<-- "fields/custom_bson_serialization.py"
```

In this example, we decide to store string data manually encoded in the ASCII encoding.
The encoding is handled in the `__bson__` class method. On top of this, we handle the
decoding by attempting to decode `bytes` object in the `validate` method.

!!! abstract "Resulting documents in the collection `example` after execution"
    ```json hl_lines="3"
    {
      "_id" : ObjectId("5f81fa5e8adaf4bf33f05035"),
      "field" : BinData(0,"aGVsbG8gd29ybGQ=")
    }
    ```

!!! warning
    When using custom bson serialization, it's important to handle as well the data
    validation for data retrieved from Mongo. In the previous example it's done by
    handling `bytes` objects in the validate method.
