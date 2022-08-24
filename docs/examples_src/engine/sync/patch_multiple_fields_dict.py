from odmantic import SyncEngine, Model


class Player(Model):
    name: str
    game: str


engine = SyncEngine()

player_tlo = engine.find_one(Player, Player.name == "TLO")
print(repr(player_tlo))
#> Player(id=ObjectId(...), name='TLO', game='Starcraft')

# Create the patch dictionary containing the new values
patch_object = {"name": "TheLittleOne", "game": "Starcraft II"}
# Update the local instance
player_tlo.update(patch_object)

print(repr(player_tlo))
#> Player(id=ObjectId(...), name='TheLittleOne', game='Starcraft II')

# Finally persist the instance
engine.save(player_tlo)
