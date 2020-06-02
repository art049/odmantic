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


z = Publisher()
z.w = 5  # FIXME: Should raise a mypy warning
