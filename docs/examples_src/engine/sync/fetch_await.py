from odmantic import SyncEngine, Model


class Player(Model):
    name: str
    game: str


engine = SyncEngine()

players = list(engine.find(Player, Player.game != "Starcraft"))
print(players)
#> [
#>     Player(id=ObjectId(...), name="Leeroy Jenkins", game="World of Warcraft"),
#>     Player(id=ObjectId(...), name="Shroud", game="Counter-Strike"),
#> ]
