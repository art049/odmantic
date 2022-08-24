from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()

delete_count = await engine.remove(Player, Player.game == "Warzone")
print(delete_count)
#> 2
