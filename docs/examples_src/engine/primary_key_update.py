from bson import ObjectId

from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()

shroud = await engine.find_one(Player, Player.name == "Shroud")
print(shroud.id)
#> 5f86074f6dfecacc68428a62
new_id = ObjectId("ffffffffffffffffffffffff")
# First delete the remote instance
await engine.delete(shroud)
# Then, copy the player object with a new primary key
new_shroud = Player(**{**shroud.dict(), "id": new_id})
# Finally create again the document
await engine.save(new_shroud)
