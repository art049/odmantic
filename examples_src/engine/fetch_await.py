from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()

players = await engine.find(Player, Player.game != "Starcraft")
print(players)
#> [
#>     Player(id=ObjectId(...), name="Leeroy Jenkins", game="World of Warcraft"),
#>     Player(id=ObjectId(...), name="Shroud", game="Counter-Strike"),
#> ]
