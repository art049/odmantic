from odmantic import SyncEngine, Model


class Player(Model):
    name: str
    game: str


engine = SyncEngine()
shroud = engine.find_one(Player, Player.name == "Shroud")
print(shroud.game)
#> Counter-Strike
shroud.game = "Valorant"
engine.save(shroud)
