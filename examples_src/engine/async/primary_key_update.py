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
# Copy the player instance with a new primary key
new_shroud = shroud.copy(update={"id": new_id})
# Delete the initial player instance
await engine.delete(shroud)
# Finally persist again the new instance
await engine.save(new_shroud)
