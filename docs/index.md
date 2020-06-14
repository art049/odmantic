# Getting started

## Defining a model

```python
from odmantic import Model


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

### Creating a session

=== "AsyncIO"

    ```python
    from motor.motor_asyncio import AsyncIOMotorClient
    from odmantic import AIOEngine

    client = AsyncIOMotorClient("mongodb://localhost:27017/")
    engine = AIOEngine(motor_client=client, db_name="example_db")
    ```

=== "Sync"

### Persisting an instance

=== "AsyncIO"

    ```python
    await engine.add(person_instance)
    ```

=== "Sync"

    ```python
    engine.add(person_instance)
    ```

## Querying instances

=== "AsyncIO"

    ```python
    freddies = await engine.find(Person, Person.first_name == "Freddie")
    for fred in freddies:
        print(fred)
    #> Person(first_name="Freddie", last_name="Mercury")
    #> Person(first_name="Freddie", last_name="Highmore")
    ```

=== "Sync"

    ```python
    freddies = engine.find(Person, Person.first_name == "Freddie")
    for fred in freddies:
        print(fred)
    #> Person(first_name="Freddie", last_name="Mercury")
    #> Person(first_name="Freddie", last_name="Highmore")
    ```
