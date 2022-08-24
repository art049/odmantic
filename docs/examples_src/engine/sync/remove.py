from odmantic import SyncEngine, Model


class Player(Model):
    name: str
    game: str


engine = SyncEngine()

delete_count = engine.remove(Player, Player.game == "Warzone")
print(delete_count)
#> 2
