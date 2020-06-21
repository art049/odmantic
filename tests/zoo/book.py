from odmantic.fields import Reference
from odmantic.model import Model


class Publisher(Model):
    name: str
    founded: int
    location: str


class Book(Model):
    title: str
    pages: int
    publisher: Publisher = Reference()
