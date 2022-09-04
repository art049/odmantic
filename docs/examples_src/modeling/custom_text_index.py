import pymongo

from odmantic import Model


class Post(Model):
    title: str
    content: str

    class Config:
        @staticmethod
        def indexes():
            yield pymongo.IndexModel(
                [(+Post.title, pymongo.TEXT), (+Post.content, pymongo.TEXT)]
            )
