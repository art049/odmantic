from pydantic import BaseModel

from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()


player_tlo = await engine.find_one(Player, Player.name == "TLO")
print(repr(player_tlo))
#> Player(id=ObjectId(...), name='TLO', game='Starcraft')

# Create the structure of the patch object with pydantic
class PatchPlayerSchema(BaseModel):
    name: str
    game: str


# Create the patch object containing the new values
patch_object = PatchPlayerSchema(name="TheLittleOne", game="Starcraft II")
# Apply the patch to the instance
player_tlo.update(patch_object)

print(repr(player_tlo))
#> Player(id=ObjectId(...), name='TheLittleOne', game='Starcraft II')

# Finally persist again the new instance
await engine.save(player_tlo)
