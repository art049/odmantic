class Publisher(Model):
    name: str
    founded: int
    location: str


class Book(Model):
    title: str
    pages: int
    publisher_ids: Tuple[ObjectId, ...]
