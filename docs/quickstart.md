# Quickstart

- Model creation with details



## Defining a model

```python
from motor.motor_asyncio import AsyncIOMotorClient

from odmantic import AIOEngine, Model


class Person(Model):
    first_name: str
    last_name: str
```

## Creating an instance

```python
person_instance = Person(first_name="Robert", last_name="Miles")
print(person_instance)
#> Person(first_name="Robert", last_name="Miles")
print(person_instance.first_name)
#> Robert
print(person_instance.last_name)
#> Miles

```

## Saving a created instance

### Creating an engine

```python

client = AsyncIOMotorClient("mongodb://localhost:27017/")
engine = AIOEngine(motor_client=client, db_name="example_db")
```

### Persisting an instance

=== "save"
    ```python
    await engine.save(Person(first_name="Freddie", last_name="Mercury"))
    await engine.save(Person(first_name="Robert", last_name="Miles"))`
    ```
=== "save_all"
    ```python
    await engine.save_all([
        Person(first_name="Freddie", last_name="Mercury"),
        Person(first_name="Robert", last_name="Miles")
    ])
    ```
## Querying instances

=== "async for"
    ```python
    cursor = engine.find(Person, Person.first_name == "Freddie")
    async for freddie in cursor:
        print(freddie)
    #> Person(first_name="Freddie", last_name="Mercury")`
    ```
=== "await"
    ```python
    freddies = await engine.find(Person, Person.first_name == "Freddie")
    print(freddies)
    #> [Person(first_name="Freddie", last_name="Mercury")]`
    ```
