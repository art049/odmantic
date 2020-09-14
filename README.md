<div align="center">
<h1>ODMantic</h1>
<a href="https://github.com/art049/odmantic/actions?query=workflow%3A%22build%22+branch%3Amaster" target="_blank">
    <img src="https://github.com/art049/odmantic/workflows/build/badge.svg" alt="build">
</a>
<a href="https://art049.github.io/odmantic/" target="_blank">
    <img src="https://github.com/art049/odmantic/workflows/docs/badge.svg" alt="docs">
</a>
<a href="https://codecov.io/gh/art049/odmantic" target="_blank">
    <img src="https://codecov.io/gh/art049/odmantic/branch/master/graph/badge.svg?token=3NYZK14STZ" alt="coverage">
</a>
<img src="https://img.shields.io/badge/python-3.6%20|%203.7%20|%203.8-informational.svg" alt="python-3.6-3.7-3.8">

<a href="https://pypi.org/project/odmantic" target="_blank">
    <img src="https://img.shields.io/pypi/v/odmantic?color=%2334D058&label=pypi" alt="Package version">
</a>
</div>

---

**Documentation**: [https://art049.github.io/odmantic/](https://art049.github.io/odmantic/)

---

ODMantic is an Object Document Mapper (a kind of ORM but for NoSQL databases) for
MongoDB based on standard python type hints. It's built on top of
[pydantic](https://pydantic-docs.helpmanual.io/) for model definition and validation.

Core features:

- **Simple**: define your model by typing your fields using python types, build queries
  using python comparison operators

- **Developer experience**: field/method autocompletion, type hints

- **Fully typed**: leverage static analysis to reduce runtime issues

- **AsyncIO**: works well with ASGI frameworks
  ([FastAPI](https://github.com/tiangolo/fastapi),
  [Starlette](https://github.com/encode/starlette), ...)

## Requirements

**Python**: 3.6 and later (tested against 3.6, 3.7 and 3.8)

**MongoDB**: 4.0 and later

Two direct dependencies:

- [pydantic](https://pydantic-docs.helpmanual.io/): makes data validation and schema
  definition both handy and elegant.

- [motor](https://motor.readthedocs.io/en/stable/): an asyncio MongoDB driver officially
  developed by the MongoDB team.

## Installation

```shell
pip install odmantic
```

## Example

### Define your first model

```python
from odmantic import Model, Field

class Publisher(Model):
    name: str
    founded: int
    location: str = None
```

### Create some instances

```python
instances = [
    Publisher(name="HarperCollins", founded=1989, location="US),
    Publisher(name="Hachette Livre", founded=1826, location="FR"),
    Publisher(name="Lulu", founded=2002)
]
```

### Populate the database with your instances

```python
from odmantic import AIOEngine

engine = AIOEngine()
await engine.save_all(instances)
```

### Find instances matching specific criteria

```python
early_publishers = await engine.find(Publisher, Publisher.founded <= 2000)
print(early_publishers)
#> [Publisher(name="HarperCollins", founded=1989, location="US),
#>  Publisher(name="Hachette Livre", founded=1826, location="FR")]
ca_publisher = await engine.find_one(Publisher, Publisher.location == "CA")
print(ca_publisher)
#> None
```

### Update an instance

```python
lulu = await engine.find_one(Publisher, Publisher.name == "Lulu")
lulu.location = "US"
print(lulu)
#> Publisher(name="Lulu", founded=2002, location="US)
await engine.save(lulu)
```

```python
lulu.founded = 1439
#> ValidationError exception raised
```

## License

This project is licensed under the terms of the [ISC license](https://en.wikipedia.org/wiki/ISC_license).
