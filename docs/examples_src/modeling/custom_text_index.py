import pymongo

from odmantic import Model


class Post(Model):
    title: str
    content: str

    model_config = {
        "indexes": lambda: [
            pymongo.IndexModel(
                [(+Post.title, pymongo.TEXT), (+Post.content, pymongo.TEXT)]
            )
        ]
    }
