from odmantic import Field, Model


class User(Model):
    name: str = Field(key_name="username")


user = User(name="John")
print(user.doc())
#> {'username': 'John', '_id': ObjectId('5f8352a87a733b8b18b0cb27')}
