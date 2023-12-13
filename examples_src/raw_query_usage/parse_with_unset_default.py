from bson import ObjectId

from odmantic import Model


class Player(Model):
    name: str
    level: int = 1


document = {"name": "Leeroy", "_id": ObjectId("5f8352a87a733b8b18b0cb27")}

user = Player.model_validate_doc(document)
print(repr(user))
#> Player(
#>     id=ObjectId("5f8352a87a733b8b18b0cb27"),
#>     name="Leeroy",
#>     level=1,
#> )
