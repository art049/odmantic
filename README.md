<div align="center">
<h1>ODMantic</h1>
<a href="https://github.com/art049/odmantic/actions?query=workflow%3A%22build%22+branch%3Amaster" target="_blank">
    <img src="https://github.com/art049/odmantic/workflows/build/badge.svg" alt="build">
</a>
<a href="https://codecov.io/gh/art049/odmantic" target="_blank">
    <img src="https://codecov.io/gh/art049/odmantic/branch/master/graph/badge.svg?token=3NYZK14STZ" alt="coverage">
</a>
<img src="https://img.shields.io/badge/python-3.6%20|%203.7%20|%203.8%20|%203.9-informational.svg" alt="python-3.6-3.7-3.8">
<a href="https://pypi.org/project/odmantic" target="_blank">
    <img src="https://img.shields.io/pypi/v/odmantic?color=%2334D058&label=pypi" alt="Package version">
</a>
<a href="https://gitter.im/odmantic/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge" target="_blank">
    <img src="https://badges.gitter.im/odmantic/community.svg" alt="Gitter">
</a>

</div>

---

**Documentation**: [https://art049.github.io/odmantic/](https://art049.github.io/odmantic/)

---

ODMantic is an Object Document Mapper (a kind of ORM but for NoSQL databases) for
MongoDB based on standard python type hints. It's built on top of
<a href="https://pydantic-docs.helpmanual.io/" target="_blank">pydantic</a> for model definition and validation.

Core features:

- **Simple**: define your model by typing your fields using python types, build queries
  using python comparison operators

- **Developer experience**: field/method autocompletion, type hints, data validation,
  perform database operations in a functional way

- **Fully typed**: leverage static analysis to reduce runtime issues

- **AsyncIO**: works well with ASGI frameworks (<a href="https://fastapi.tiangolo.com/"
  target="_blank">FastAPI</a>, <a href="https://www.starlette.io/"
  target="_blank">Starlette</a>, ...)

- **Serialization**: built in JSON serialization and JSON schema generation

## Requirements

**Python**: 3.6 and later (tested against 3.6, 3.7, 3.8 and 3.9)

**MongoDB**: 4.0 and later

Two direct dependencies:

- <a href="https://pydantic-docs.helpmanual.io/" target="_blank">pydantic</a>: makes
  data validation and schema definition both handy and elegant.

- <a href="https://motor.readthedocs.io/en/stable/" target="_blank">motor</a>: an
  asyncio MongoDB driver officially developed by the MongoDB team.

## Installation

```shell
pip install odmantic
```

## Example

> To enjoy an async context without any code boilerplate, you can reproduce the
> following steps using the AsyncIO REPL (only for Python 3.8+).
>
> ```
> python3.8 -m asyncio
> ```
>
> If you are using an earlier version of Python you can use <a
> href="https://ipython.readthedocs.io/en/stable/install/index.html"
> target="_blank">IPython</a> which provide an Autoawait feature (starting from Python
> 3.6).

### Define your first model

```python
from typing import Optional

from odmantic import Field, Model


class Publisher(Model):
    name: str
    founded: int = Field(ge=1440)
    location: Optional[str] = None
```

By defining the `Publisher` class, we've just created an ODMantic model 🎉. In this
example, the model will represent book publishers.

This model contains three fields:

- `name`: This is the name of the Publisher. This is a simple string field without any
  specific validation but it will be required to build a new Publisher.

- `founded`: This is the year of foundation of the Publisher. Since the printing press
  has been invented in 1440, it would be handy to allow only values above 1440. The
  `ge` keyword argument passed to the Field is exactly doing this. The model will
  require a founded value greater or equal than 1440.

- `location`: This field will contain the country code of the Publisher. Defining this
  field as `Optional` with a `None` default value makes it a non required field that
  will be set automatically when not specified.

The collection name has been defined by ODMantic as well. In this case it will be
`publisher`.

### Create some instances

```python
instances = [
    Publisher(name="HarperCollins", founded=1989, location="US"),
    Publisher(name="Hachette Livre", founded=1826, location="FR"),
    Publisher(name="Lulu", founded=2002)
]
```

We defined three instances of the Publisher model. They all have a `name` property as it
was required. All the foundations years are later than 1440. The last publisher has no
location specified so by default this field is set to `None` (it will be stored as
`null` in the database).

For now, those instances only exists locally. We will persist them in a database in the
next step.

### Populate the database with your instances

> For the next steps, you'll need to start a local MongoDB server.The easiest way is
> to use docker. Simply run the next command in a terminal (closing the terminal will
> terminate the MongoDB instance and remove the container).
>
> ```shell
> docker run --rm --net=host mongo
> ```

First, let's connect to the database using the engine. In ODMantic, every database
operation is performed using the engine object.

```python
from odmantic import AIOEngine

engine = AIOEngine()
```

By default, the `AIOEngine` (stands for AsyncIOEngine) automatically tries to connect to a
MongoDB instance running locally (on port 27017). Since we didn't provide any database name, it will use
the database named `test` by default.

The next step is to persist the instances we created before. We can perform this
operation using the `AIOEngine.save_all` method.

```python
await engine.save_all(instances)
```

Most of the engine I/O methods are asynchronous, hence the `await` keyword used here.
Once the operation is complete, we should be able to see our created documents in the
database. You can use <a href="https://www.mongodb.com/products/compass"
target="_blank">Compass</a> or <a href="https://robomongo.org/"
target="_blank">RoboMongo</a> if you'd like to have a graphical interface.

Another possibility is to use `mongo` CLI directly:

```shell
mongo --eval "db.publisher.find({})"
```

Output:

```json
connecting to: mongodb://127.0.0.1:27017
{
  "_id": ObjectId("5f67b331514d6855bc5c54c9"),
  "founded": 1989,
  "location": "US",
  "name": "HarperCollins"
},
{
  "_id": ObjectId("5f67b331514d6855bc5c54ca"),
  "founded":1826,
  "location": "FR",
  "name": "Hachette Livre"
},
{
  "_id": ObjectId("5f67b331514d6855bc5c54cb"),
  "founded": 2002,
  "location": null,
  "name": "Lulu"
}
```

The created instances are stored in the `test` database under the `publisher` collection.

We can see that an `_id` field has been added to each document. MongoDB need this field
to act as a primary key. Actually, this field is added by ODMantic and you can access it
under the name `id`.

```python
print(instances[0].id)
#> ObjectId("5f67b331514d6855bc5c54c9")
```

### Find instances matching a criteria

Since we now have some documents in the database, we can start building some queries.

First, let's find publishers created before the 2000s:

```python
early_publishers = await engine.find(Publisher, Publisher.founded <= 2000)
print(early_publishers)
#> [Publisher(name="HarperCollins", founded=1989, location="US),
#>  Publisher(name="Hachette Livre", founded=1826, location="FR")]
```

Here, we called the `engine.find` method. The first argument we need to specify is the
Model class we want to query on (in our case `Publisher`). The second argument is the
actual query. Similarly to <a href="https://www.sqlalchemy.org/"
target="_blank">SQLAlchemy</a>, you can build ODMantic queries using the regular python
operators.

When awaited, the `engine.find` method will return the list of matching instances stored
in the database.

Another possibility is to query for at most one instance. For example, if we want to
retrieve a publisher from Canada (CA):

```python
ca_publisher = await engine.find_one(Publisher, Publisher.location == "CA")
print(ca_publisher)
#> None
```

Here the result is `None` because no matching instances have been found in the database.
The `engine.find_one` method returns an instance if one exists in the database
otherwise, it will return `None`.

### Modify an instance

Finally, let's edit some instances. For example, we can set the `location` for the
publisher named `Lulu`.
First, we need to gather the instance from the database:

```python
lulu = await engine.find_one(Publisher, Publisher.name == "Lulu")
print(lulu)
#> Publisher(name="Lulu", founded=2002, location=None)
```

We still have the same instance, with no location set. We can change this field:

```python
lulu.location = "US"
print(lulu)
#> Publisher(name="Lulu", founded=2002, location="US)
```

The location has been changed locally but the last step to persist this change is to
save the document:

```python
await engine.save(lulu)
```

We can now check the database state:

```shell
mongo --eval "db.publisher.find({name: 'Lulu'})"
```

Output:

```json hl_lines="5"
connecting to: mongodb://127.0.0.1:27017
{
  "_id": ObjectId("5f67b331514d6855bc5c54cb"),
  "founded": 2002,
  "location": "US",
  "name": "Lulu"
}
```

The document have been successfully updated !

Now, what if we would like to change the foundation date with an invalid one (before 1440) ?

```python
lulu.founded = 1000
#> ValidationError: 1 validation error for Publisher
#> founded
#>   ensure this value is greater than 1440
#>   (type=value_error.number.not_gt; limit_value=1440)
```

This will raise an exception as it's not matching the model definition. The raised
exception is actually a `ValidationError` created by from <a
href="https://pydantic-docs.helpmanual.io/usage/models/#error-handling"
target="_blank">pydantic</a>.

### Next steps

If you already have experience with Pydantic and FastAPI, the [Usage with FastAPI](https://art049.github.io/odmantic/usage_fastapi/) example might be interesting for you.

Otherwise, to get started on more advanced practices like relations and building more
advanced queries, you can directly check the other sections of the
[documentation](https://art049.github.io/odmantic/).

If you wish to contribute to the project (Thank you! :smiley:), you can have a look to the
[Contributing](https://art049.github.io/odmantic/contributing/) section of the
documentation.

## License

This project is licensed under the terms of the <a
href="https://github.com/art049/odmantic/blob/master/LICENSE" target="_blank">ISC license</a>.
