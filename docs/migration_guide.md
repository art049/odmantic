# Migration Guide

## Migrating to v1

Before migrating ODMantic, have a look at the [Pydantic v2 migration guide](https://docs.pydantic.dev/dev/migration/).

### Upgrading to ODMantic v1

```bash
pip install -U pydantic
```

### Handling `Optional` with non-implicit default `None` values

Since this new version, the default value of an `Optional` field is not implicit anymore.
Thus, if you want to keep the same behavior, you have to add the `default` parameter to your `Optional` fields.

**Before:**

```python hl_lines="2"
class MyModel(Model):
    my_field: Optional[str]

assert MyModel().my_field is None
```

**Now:**


```python hl_lines="2"
class MyModel(Model):
    my_field: Optional[str] = None

assert MyModel().my_field is None
```

### Upgrading models configuration

Instead of the old `Config` class, you have to use the new `model_config` typed dict.

**Before:**

```python
class Event(Model):
    date: datetime

    class Config:
        collection = "event_collection"
        parse_doc_with_default_factories = True
        indexes = [
            Index(Event.date, unique=True),
            pymongo.IndexModel([("date", pymongo.DESCENDING)]),
        ]
```

**Now:**
```python
class Event(Model):
    date: datetime

    model_config = {
        "collection": "event_collection",
        "parse_doc_with_default_factories": True,
        "indexes": lambda: [
            Index(Event.date, unique=True),
            pymongo.IndexModel([("date", pymongo.DESCENDING)]),
        ],
    }
```

### Defining custom BSON serializers

Instead of using the `__bson__` class method, you have to use the new [WithBsonSerializer][odmantic.bson.WithBsonSerializer] annotation.

!!! note
    We will probably bring back the `__bson__` class method in a future version but
    using the new annotation is the recommended way to define custom BSON serializers.

Here is an example of serializing an integer as a string in BSON:

**Before:**

```python
class IntBSONStr(int):
    @classmethod
    def __bson__(cls, v) -> str:
        return str(v)
```

**Now:**

```python
from typing import Annotated
from odmantic import WithBsonSerializer

IntBSONStr = Annotated[int, WithBsonSerializer(lambda v: str(v))]
```


### Building a Pydantic model from an ODMantic model

If you want to build a Pydantic model from an ODMantic model, you now have to enable the
[`from_attributes`](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.from_attributes){target="_blank"} configuration option.

For example, with a `UserModel` that is used internally and a `ResponseSchema` that
could be exposed through an API:

```python hl_lines="14"
from pydantic import BaseModel, EmailStr
from odmantic import Model

class UserModel(Model):
    email: EmailStr
    password_hash: str

class UserSchema(BaseModel):
    email: EmailStr

class ResponseSchema(BaseModel):
    user: UserSchema

    model_config = {"from_attributes": True}

user = UserModel(email="john@doe.com", password_hash="...")
response = ResponseSchema(user=user)
```


### Replacing the `Model` and `EmbeddedModel` deprecated methods

- Replace `Model.dict` with the new `Model.model_dump` method

- Replace `Model.doc` with the new `Model.model_dump_doc` method

- Replace `Model.parse_doc` with the new `Model.model_validate_doc` method

- Replace `Model.update` with the new `Model.model_update` method

- Replace `Model.copy` with the new `Model.model_copy` method

### Custom JSON encoders on `odmantic.bson` types

Custom JSON encoders (defined with the `json_encoders` config option) are no longer
effective on `odmantic.bson` types since the builtin encoders cannot be overridden in
that way anymore.

The solution is to use the PlainSerializer annotation provided by Pydantic. For example,
if we want to serialize ObjectId as a `id_` prefixed string:

```python hl_lines="5 12"
from typing import Annotated
from pydantic import BaseModel, PlainSerializer
from odmantic import ObjectId

MyObjectId = Annotated[ObjectId, PlainSerializer(lambda v: "id_" + str(v))]

class MyModel(BaseModel):
    id: MyObjectId

instance = MyModel(id=ObjectId("ffffffffffffffffffffffff"))
print(instance.model_dump_json())
#> {"id": "id_ffffffffffffffffffffffff"}
```


---

And ... that's it, congrats! 🚀⚒️

If you have any questions or if you need help to migrate something that is not covered
by this guide, feel free to open an issue on [GitHub](https://github.com/art049/odmantic/issues){target="_blank"}.
