from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()
shroud = await engine.find_one(Player, Player.name == "Shroud")
print(shroud.game)
#> Counter-Strike
shroud.game = "Valorant"
await engine.save(shroud)
