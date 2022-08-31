# Engine

This engine documentation present how to work with both the Sync ([SyncEngine][odmantic.engine.SyncEngine]) and the Async ([AIOEngine][odmantic.engine.AIOEngine]) engines. The methods available for both are very close but the main difference is that the Async engine exposes coroutines instead of functions for the Sync engine.

## Creating the engine

In the previous examples, we created the engine using default parameters:

- MongoDB: running on `localhost` port `27017`

- Database name: `test`

It's possible to provide a custom client ([AsyncIOMotorClient](https://motor.readthedocs.io/en/stable/api-asyncio/asyncio_motor_client.html){:target=blank_} or [PyMongoClient](https://pymongo.readthedocs.io/en/stable/api/pymongo/mongo_client.html){:target=blank_}) to the engine constructor. In the same way, the database name can be changed using the `database` keyword argument.

{{ async_sync_snippet("engine", "engine_creation.py") }}

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

- `engine.save`: to save a single instance

- `engine.save_all`: to save multiple instances at
  once

{{ async_sync_snippet("engine", "create.py", hl_lines="12 19") }}

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
    When calling `engine.save` or
    `engine.save_all`, the referenced models will are persisted
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
`engine.find_one` method to get at most one
instance of a specific Model. This method will either return an instance matching the
specified criteriums or `None` if no instances have been found.

{{ async_sync_snippet("engine", "fetch_find_one.py", hl_lines="11 15-17") }}

!!! info "Missing values in documents"
    While parsing the MongoDB documents into Model instances, ODMantic will use the
    provided default values to populate the missing fields.

    See [this section](raw_query_usage.md#advanced-parsing-behavior) for more details about document parsing.

!!! tip "Fetch using `sort`"
    We can use the `sort` parameter to fetch the `Player` instance with
    the first `name` in ascending order:
    ```python
    await engine.find_one(Player, sort=Player.name)
    ```
    Find out more on `sort` in [the dedicated section](querying.md#sorting).

### Fetch multiple instances

To get more than one instance from the database at once, you can use the
`engine.find` method.

This method will return a cursor: an [AIOCursor][odmantic.engine.AIOCursor] object for the [AIOEngine][odmantic.engine.AIOEngine] and a [SyncCursor][odmantic.engine.SyncCursor] object for the [SyncEngine][odmantic.engine.SyncEngine].

Those cursors can mainly be used in two different ways:
#### Usage as an iterator

{{ async_sync_snippet("engine", "fetch_async_for.py", hl_lines="11") }}


!!! tip "Ordering instances"
    The `sort` parameter allows to order the query in ascending or descending order on
    a single or multiple fields.
    ```python
    engine.find(Player, sort=(Player.name, Player.game.desc()))
    ```
    Find out more on `sort` in [the dedicated section](querying.md#sorting).

#### Usage as an awaitable/list

Even if the iterator usage should be preferred, in some cases it might be required
to gather all the documents from the database before processing them.

{{ async_sync_snippet("engine", "fetch_await.py", hl_lines="11") }}

!!! note "Pagination"
    When using [AIOEngine.find][odmantic.engine.AIOEngine.find] or [SyncEngine.find][odmantic.engine.SyncEngine.find]
    you can as well use the `skip` and `limit` keyword arguments , respectively to skip
    a specified number of instances and to limit the number of fetched instances.

!!! tip "Referenced instances"
    When calling `engine.find` or `engine.find_one`, the referenced models will
    be recursively resolved as well by design.

!!! info "Passing the model class to `find` and `find_one`"
    When using the method to retrieve instances from the database, you have to specify
    the Model you want to query on as the first positional parameter. Internally, this
    enables ODMantic to properly type the results.

### Count instances

You can count instances in the database by using the `engine.count` method and as with
other read methods, it's still possible to use this method with filtering queries.

{{ async_sync_snippet("engine", "count.py", hl_lines="11 14 17") }}

!!! tip "Combining multiple queries in read operations"
    While using [find][odmantic.engine.AIOEngine.find],
    [find_one][odmantic.engine.AIOEngine.find_one] or
    [count][odmantic.engine.AIOEngine.count], you may pass as many queries as you want
    as positional arguments. Those will be implicitly combined as single
    [and_][odmantic.query.and_] query.

## Update

Updating an instance in the database can be done by modifying the instance locally and
saving it again to the database.

The `engine.save` and `engine.save_all` methods are actually behaving as
`upsert` operations. In other words, if the instance already exists it will be updated.
Otherwise, the related document will be created in the database.

### Modifying one field

Modifying a single field can be achieved by directly changing the instance attribute and
saving the instance.

{{ async_sync_snippet("engine", "update.py", hl_lines="13-14") }}

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
### Patching multiple fields at once

The easiest way to change multiple fields at once is to use the
[Model.update][odmantic.model._BaseODMModel.update] method. This method will take either a
Pydantic object or a dictionary and update the matching fields of the instance.

#### From a Pydantic Model

    {{ async_sync_snippet("engine", "patch_multiple_fields_pydantic.py", hl_lines="19-21 25 27 30 33") }}

#### From a dictionary

    {{ async_sync_snippet("engine", "patch_multiple_fields_dict.py", hl_lines="16 18 21 24") }}

!!! abstract "Resulting document associated to the player"
    ```json hl_lines="3 4"
    {
      "_id": ObjectId("5f85f36d6dfecacc68428a49"),
      "game": "Starcraft II",
      "name": "TheLittleOne"
    }
    ```

### Changing the primary field

Directly changing the primary field value as explained above is not
possible and a `NotImplementedError` exception will be raised if you try to do so.

The easiest way to change an instance primary field is to perform a local copy of the
instance using the [Model.copy][odmantic.model._BaseODMModel.copy] method.

{{ async_sync_snippet("engine", "primary_key_update.py", hl_lines="18 20 22") }}

!!! abstract "Resulting document associated to the player"
    ```json hl_lines="2"
    {
        "_id": ObjectId("ffffffffffffffffffffffff"),
        "game": "Valorant",
        "name": "Shroud"
    }
    ```

!!! danger "Update data used with the copy"
    The data updated by the copy method is not validated: you should **absolutely**
    trust this data.



## Delete

### Delete a single instance

You can delete instance by passing them to the `engine.delete` method.

{{ async_sync_snippet("engine", "delete.py", hl_lines="14") }}

### Remove

You can delete instances that match a filter by using the
`engine.remove` method.

{{ async_sync_snippet("engine", "remove.py", hl_lines="11") }}


#### Just one

You can limit `engine.remove` to removing only one
instance by passing `just_one`.

{{ async_sync_snippet("engine", "remove_just_one.py", hl_lines="12") }}
## Consistency


### Using a Session

!!! Tip "Why are sessions needed ?"
    A session is a way to
    guarantee that the data you read is consistent with the data you write.
    This is especially useful when you need to perform multiple operations on the
    same data.

    See [this document](https://www.mongodb.com/docs/manual/core/read-isolation-consistency-recency/#causal-consistency){:target=blank_} for more details on causal consistency.

You can create a session by using the `engine.session` method. This method will return
either a [SyncSession][odmantic.session.SyncSession] or an
[AIOSession][odmantic.session.AIOSession] object, depending on the type of engine used.
Those session objects are context manager and can be used along with the `with` or the
`async with` keywords. Once the context is entered the `session` object exposes the same
database operation methods as the related `engine` object but execute each operation in
the session context.


{{ async_sync_snippet("engine", "save_with_session.py", hl_lines="13-23") }}

!!! Tip "Directly using driver sessions"
    Every single engine method also accepts a `session` parameter. You can use this
    parameter to provide an existing driver (motor or PyMongo) session that you created
    manually.

!!! Tip "Accessing the underlying driver session object"
    The `session.get_driver_session` method exposes the underlying driver session. This
    is useful if you want to use the driver session directly to perform raw operations.

### Using a Transaction

!!! Tip "Why are transactions needed ?"
    A transaction is a mechanism that allows you to execute multiple operations in a
    single atomic operation. This is useful when you want to ensure that a set of
    operations is atomicly performed on a specific document.

!!! Error "MongoDB transaction support"
    Transactions are only supported in a replica sets (Mongo 4.0+) or sharded clusters
    with replication enabled (Mongo 4.2+), if you use them in a standalone MongoDB
    instance an error will be raised.

You can create a transaction directly from the engine by using the `engine.transaction`
method. This methods will either return a
[SyncTransaction][odmantic.session.SyncTransaction] or an
[AIOTransaction][odmantic.session.AIOTransaction] object. As for sessions, transaction
objects exposes the same database operation methods as the related `engine` object but
execute each operation in a transactional context.

In order to terminate a transaction you must either call the `commit` method to persist
all the changes or call the `abort` method to drop the changes introduced in the
transaction.

{{ async_sync_snippet("engine", "save_with_transaction.py", hl_lines="11-13 18-21") }}

It is also possible to create a transaction within an existing session by using
the `session.transaction` method:
{{ async_sync_snippet("engine", "transaction_from_session.py", hl_lines="11-19") }}
