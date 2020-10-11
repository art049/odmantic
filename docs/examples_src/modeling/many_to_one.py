from odmantic import AIOEngine, Model, Reference


class Publisher(Model):
    name: str
    founded: int
    location: str


class Book(Model):
    title: str
    pages: int
    publisher: Publisher = Reference()


hachette = Publisher(name="Hachette Livre", founded=1826, location="FR")
harper = Publisher(name="HarperCollins", founded=1989, location="US")

books = [
    Book(title="They Didn't See Us Coming", pages=304, publisher=hachette),
    Book(title="This Isn't Happening", pages=256, publisher=hachette),
    Book(title="Prodigal Summer", pages=464, publisher=harper),
]

engine = AIOEngine()
await engine.save_all(books)
