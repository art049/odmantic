from odmantic.model import Model
from odmantic.reference import Reference


class Publisher(Model):
    name: str
    founded: int
    location: str


class Book(Model):
    title: str
    pages: int
    publisher: Publisher = Reference()
