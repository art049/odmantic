# Raw query usage

As ODMantic doesn't completely wrap the MongoDB API, some helpers are provided to be
enhance the usability while building raw queries and interacting with raw documents.

## Raw query helpers

### Collection name
You can get the collection name associated to a model by using the unary `+` operator on
the model class.
```python linenums="1"
--8<-- "raw_query_usage/collection_name.py"
```

### Motor collection
The [AIOEngine][odmantic.engine.AIOEngine] object can provide you directly the motor
collection
([AsyncIOMotorCollection](https://motor.readthedocs.io/en/stable/api-asyncio/asyncio_motor_collection.html){:target=blank_})
linked to the motor client used by the engine. To achieve this, you can use the
[AIOEngine.get_collection][odmantic.engine.AIOEngine.get_collection] method.

```python linenums="1" hl_lines="9"
--8<-- "raw_query_usage/motor_collection.py"
```

### Key name of a field
Since some field might have some [customized key names](fields.md#document-structure),
you can get the key name associated to a field by using the unary `+` operator on the
model class. As well, to ease the use of aggregation pipelines where you might need to
reference your field (`$field`), you can double the operator (i.e use `++`) to get the
field reference name.

```python linenums="1"
--8<-- "raw_query_usage/field_key_name.py"
```

## Creating instances from a raw documents
You can parse MongoDB document to instances using the
[parse_doc][odmantic.model._BaseODMModel.parse_doc] method.

!!! note
    If the provided documents contain extra fields, ODMantic will ignore them. This can
    be especially useful in aggregation pipelines.

```python linenums="1" hl_lines="20 27 38-39 44"
--8<-- "raw_query_usage/create_from_raw.py"
```
## Extract documents from existing instances
You can generate a document from instances using the
[doc][odmantic.model._BaseODMModel.doc] method.
```python linenums="1" hl_lines="20 27 38-39 44"
--8<-- "raw_query_usage/extract_from_raw.py"
```
## Aggregation example
In the following example, we will demonstrate the use of the previous helpers to build
an aggregation pipeline. We will first consider a `Rectangle` model with two float
fields (`height` and `length`). We will then fetch the rectangles with an area that is
less than 10. To finish, we will reconstruct `Rectangle` instances from this query.

```python linenums="1" hl_lines="20 27 38-39 44"
--8<-- "raw_query_usage/aggregation_example.py"
```
