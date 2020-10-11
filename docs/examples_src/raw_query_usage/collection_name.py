from odmantic import Model


class User(Model):
    name: str


collection_name = +User
print(collection_name)
#> user
