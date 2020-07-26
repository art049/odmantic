# Fields

## Providing default values

```python hl_lines="3"
class Player(Model):
    name: str
    level: int = 0

p = Player(name="Zerator")
print(p)
#> Player(name="Zerator", level=0)

```

<!-- prettier-ignore -->
!!! note
    For `typing.Optional` fields, `None` is already set to the default value

## Customize Mongo document naming

```python hl_lines="2"
class Player(Model):
    name: str = field(mongo_name="nickname")

engine.save(Player(name="Jack"))
```

Resulting document:

```json
{
    "_id": ObjectId("5ed50fcad11d1975aa3d7a28"), # See the next section for more details
    "nickname": "Jack",
}
```

<!-- prettier-ignore -->
!!! tip
    You can combine default values and custom field name by using the `default` keyword argument when building the field
    ``` python hl_lines="3"
    class Player(Model):
        name: str
        level: int = field(default=0, mongo_name="lvl")
    ```

## Primary key definition

### Implicit

If not explicitly declared, an `id` primary key will be added to each model (corresponding to the `_id` key in Mongo documents).
This key will be populated when the instances are saved or fetched.

```python
class Player(Model):
    name: str

leeroy = Player(name="Leeroy Jenkins")
await engine.save(leeroy)
print(leeroy)
#> Player(id=ObjectId('5ed50fcad11d1975aa3d7a28'), name="Leeroy Jenkins")
```

### Explicit

If you want to use a field as the primary key

<!-- prettier-ignore -->
!!! warning
    The Mongo name of the primary key field will be enforced to `_id`

```python hl_lines="2"
class Player(Model):
    name: str = field(primary_key=True)

leeroy = Player(name="Leeroy Jenkins")
await engine.save(leeroy)
print(leeroy)
#> Player(name="Leeroy Jenkins")

```

Resulting document:

```json
{
  "_id": "Leeroy Jenkins"
}
```
