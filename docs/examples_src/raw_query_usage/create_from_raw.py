from bson import ObjectId

from odmantic import Field, Model


class User(Model):
    name: str = Field(key_name="username")


document = {"username": "John", "_id": ObjectId("5f8352a87a733b8b18b0cb27")}

user = User.model_validate_doc(document)
print(repr(user))
#> User(id=ObjectId('5f8352a87a733b8b18b0cb27'), name='John')
