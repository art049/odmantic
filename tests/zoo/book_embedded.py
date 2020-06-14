from odmantic.model import EmbeddedModel, Model


class Publisher(EmbeddedModel):
    name: str
    founded: int
    location: str


class Book(Model):
    title: str
    pages: int
    publisher: Publisher
