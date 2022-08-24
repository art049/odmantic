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

### PyMongo collection
The [SyncEngine][odmantic.engine.SyncEngine] object can provide you directly the PyMongo
collection
([pymongo.collection.Collection](https://pymongo.readthedocs.io/en/stable/api/pymongo/collection.html){:target=blank_})
linked to the PyMongo client used by the engine. To achieve this, you can use the
[SyncEngine.get_collection][odmantic.engine.SyncEngine.get_collection] method.

```python linenums="1" hl_lines="9"
--8<-- "raw_query_usage/pymongo_collection.py"
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

## Using raw MongoDB filters
Any [QueryExpression][odmantic.query.QueryExpression] can be replaced by its raw filter
equivalent.

For example, with a Tree model:

```python linenums="1"
--8<-- "raw_query_usage/raw_query_filters.py"
```

All the following find queries would give exactly the same results:
```python
--8<-- "raw_query_usage/raw_query_filters_1.py"
```

## Raw MongoDB documents
### Parsing documents
You can parse MongoDB document to instances using the
[parse_doc][odmantic.model._BaseODMModel.parse_doc] method.

!!! tip
    If the provided documents contain extra fields, ODMantic will ignore them. This can
    be especially useful in aggregation pipelines.

```python linenums="1" hl_lines="20 27 38-39 44"
--8<-- "raw_query_usage/create_from_raw.py"
```


### Dumping documents
You can generate a document from instances using the
[doc][odmantic.model._BaseODMModel.doc] method.
```python linenums="1" hl_lines="20 27 38-39 44"
--8<-- "raw_query_usage/extract_from_existing.py"
```

### Advanced parsing behavior

#### Default values
While parsing documents, ODMantic will use the default values provided in the Models to populate the missing fields from the documents:

```python linenums="1" hl_lines="8 11 18"
--8<-- "raw_query_usage/parse_with_unset_default.py"
```

#### Default factories

For the field with default factories provided through the Field descriptor though, by
default they wont be populated.

```python linenums="1" hl_lines="12 15 21-24"
--8<-- "raw_query_usage/parse_with_unset_default_factory.py"
```

In the previous example, using the default factories could create data inconsistencies
and in this case, it would probably be more suitable to perform a manual migration to
provide the correct values.

Still, the `parse_doc_with_default_factories`
[Config](modeling.md#advanced-configuration) option can be used to allow the use of the
default factories while parsing documents:

```python linenums="1" hl_lines="12 15 18 25"
--8<-- "raw_query_usage/parse_with_unset_default_factory_enabled.py"
```

## Aggregation example
In the following example, we will demonstrate the use of the previous helpers to build
an aggregation pipeline. We will first consider a `Rectangle` model with two float
fields (`height` and `length`). We will then fetch the rectangles with an area that is
less than 10. To finish, we will reconstruct `Rectangle` instances from this query.

```python linenums="1" hl_lines="20 27 38-39 44"
--8<-- "raw_query_usage/aggregation_example.py"
```
