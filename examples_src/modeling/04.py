from typing import List

from bson import ObjectId

from odmantic import AIOEngine, Model


class Author(Model):
    name: str


class Book(Model):
    title: str
    pages: int
    author_ids: List[ObjectId]


david = Author(name="David Beazley")
brian = Author(name="Brian K. Jones")

python_cookbook = Book(
    title="Python Cookbook", pages=706, author_ids=[david.id, brian.id]
)
python_essentials = Book(
    title="Python Essential Reference", pages=717, author_ids=[brian.id]
)

engine = AIOEngine()
await engine.save_all((david, brian))
await engine.save_all((python_cookbook, python_essentials))
