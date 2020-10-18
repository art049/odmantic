# Engine

## Creating the engine

In the previous examples, we created the engine using default parameters:

- MongoDB: running on `localhost` port `27017`

- Database name: `test`

It's possible to provide a custom
[AsyncIOMotorClient](https://motor.readthedocs.io/en/stable/api-asyncio/asyncio_motor_client.html){:target=blank_}
to the [AIOEngine][odmantic.engine.AIOEngine] constructor. In the same way, the database
name can be changed using the `database` keyword argument.

```python linenums="1"
--8<-- "engine/engine_creation.py"
```

For additional information about the MongoDB connection strings, see [this
section](https://docs.mongodb.com/manual/reference/connection-string/){:target=blank_}
of the MongoDB documentation.

!!! tip "Usage with DNS SRV records"
    If you decide to use the [DNS Seed List Connection
    Format](https://docs.mongodb.com/manual/reference/connection-string/#dns-seed-list-connection-format){:target=blank}
    (i.e `mongodb+srv://...`), you will need to install the
    [dnspython](https://pypi.org/project/dnspython/){:target=blank_} package.

## Create
There are two ways of persisting instances to the database (i.e creating new documents):

- [AIOEngine.save][odmantic.engine.AIOEngine.save]: to save a single instance

- [AIOEngine.save_all][odmantic.engine.AIOEngine.save]: to save multiple instances at
  once

```python linenums="1" hl_lines="12 19"
--8<-- "engine/create.py"
```

??? abstract "Resulting documents in the `player` collection"
    ```json
    {
      "_id": ObjectId("5f85f36d6dfecacc68428a46"),
      "game": "World of Warcraft",
      "name": "Leeroy Jenkins"
    }
    {
      "_id": ObjectId("5f85f36d6dfecacc68428a47"),
      "game": "Counter-Strike",
      "name": "Shroud"
    }
    {
      "_id": ObjectId("5f85f36d6dfecacc68428a49"),
      "game": "Starcraft",
      "name": "TLO"
    }
    {
      "_id": ObjectId("5f85f36d6dfecacc68428a48"),
      "game": "Starcraft",
      "name": "Serral"
    }
    ```

!!! tip "Referenced instances"
    When calling [AIOEngine.save][odmantic.engine.AIOEngine.save] or
    [AIOEngine.save_all][odmantic.engine.AIOEngine.save], the referenced models will be persisted
    as well.

!!! warning "Upsert behavior"
    The `save` and `save_all` methods behave as upsert operations ([more
    details](engine.md#update)). Hence, you might overwrite documents if you save
    instances with an existing primary key already existing in the database.

## Read

!!! note "Examples database content"
    The next examples will consider that you have a `player` collection populated with
    the documents previously created.

### Fetch a single instance

As with regular MongoDB driver, you can use the
[AIOEngine.find_one][odmantic.engine.AIOEngine.find_one] method to get at most one
instance of a specific Model. This method will either return an instance matching the
specified criteriums or `None` if no instances have been found.

```python linenums="1" hl_lines="11 15-17"
--8<-- "engine/fetch_find_one.py"
```

### Fetch multiple instances

To get more than one instance from the database at once, you can use the
[AIOEngine.find][odmantic.engine.AIOEngine.find] method.

This method will return an [AIOCursor][odmantic.engine.AIOCursor] object, that can be
used in two different ways.

#### Usage as an async iterator
```python linenums="1" hl_lines="11"
--8<-- "engine/fetch_async_for.py"
```

#### Usage as an awaitable

Even if the async iterator usage should be preferred, in some cases it might be required
to gather all the documents from the database before processing them.

```python linenums="1" hl_lines="11"
--8<-- "engine/fetch_await.py"
```

!!! note "Pagination"
    You can as well use the `skip` and `limit` keyword arguments when using
    [AIOEngine.find][odmantic.engine.AIOEngine.find], respectively to skip a specified
    number of instances and to limit the number of fetched instances.

!!! tip "Referenced instances"
    When calling [AIOEngine.find][odmantic.engine.AIOEngine.find] or
    [AIOEngine.find_one][odmantic.engine.AIOEngine.find_one], the referenced models will
    be recursively resolved as well.

!!! info "Passing the model class to `find` and `find_one`"
    When using the method to retrieve instances from the database, you have to specify
    the Model you want to query on as the first positional parameter. Internally, this
    enables ODMantic to properly type the results.

### Count instances

You can count instances in the database by using the
[AIOEngine.count][odmantic.engine.AIOEngine.count] method. It's possible as well to use
this method with filtering queries.

```python linenums="1" hl_lines="11 14 17"
--8<-- "engine/count.py"
```

!!! tip "Combining multiple queries in read operations"
    While using [find][odmantic.engine.AIOEngine.find],
    [find_one][odmantic.engine.AIOEngine.find_one] or
    [count][odmantic.engine.AIOEngine.count], you may pass as many queries as you want
    as positional arguments. Those will be implicitly combined as single
    [and_][odmantic.query.and_] query.

## Update

Updating an instance in the database can be done simply by modifying the instance
locally and saving it again to the database.

The [AIOEngine.save][odmantic.engine.AIOEngine.save] and
[AIOEngine.save_all][odmantic.engine.AIOEngine.save] methods are actually behaving as
`upsert` operations. In other words, if the instance already exists it will be updated.
Otherwise, the related document will be created in the database.

```python linenums="1" hl_lines="13-14"
--8<-- "engine/update.py"
```

???+abstract "Resulting documents in the `player` collection"
    ```json hl_lines="6-10"
    {
      "_id": ObjectId("5f85f36d6dfecacc68428a46"),
      "game": "World of Warcraft",
      "name": "Leeroy Jenkins"
    }
    {
      "_id": ObjectId("5f85f36d6dfecacc68428a47"),
      "game": "Valorant",
      "name": "Shroud"
    }
    {
      "_id": ObjectId("5f85f36d6dfecacc68428a49"),
      "game": "Starcraft",
      "name": "TLO"
    }
    {
      "_id": ObjectId("5f85f36d6dfecacc68428a48"),
      "game": "Starcraft",
      "name": "Serral"
    }
    ```

!!! warning "Primary field update"
    Currently, changing the primary field value is disabled and a `NotImplementedError`
    exception will be raised if you try to do so. It is still possible to mutate the
    primary field if the field type is mutable but it might result in unexpected
    behaviors.

    ??? tip "Workaround to modify the primary key"
        There is still a workaround to update the primary key of a document:
        ```python linenums="1" hl_lines="18 20 22"
        --8<-- "engine/primary_key_update.py"
        ```

        !!! abstract "Resulting document associated to the player"
            ```json hl_lines="2"
            {
                "_id": ObjectId("ffffffffffffffffffffffff"),
                "game": "Valorant",
                "name": "Shroud"
            }
            ```

## Delete

You can delete instance by passing them to the
[AIOEngine.delete][odmantic.engine.AIOEngine.delete] method.

```python linenums="1" hl_lines="14"
--8<-- "engine/delete.py"
```

The collection is now empty :broom:.
