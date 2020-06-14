# Modeling

## Relations ?

## Embedded Models

```python hl_lines="1 9"
class Publisher(Model):
    name: str
    founded: int
    location: str

class Book(Model):
    title: str
    pages: int
    publisher: Publisher
```

## Referenced Models

```python hl_lines="9"
class Publisher(Model):
    name: str
    founded: int
    location: str

class Book(Model):
    title: str
    pages: int
    publisher: Publisher = Reference()
```
