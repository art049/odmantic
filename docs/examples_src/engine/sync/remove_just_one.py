from odmantic import Model, SyncEngine


class Player(Model):
    name: str
    game: str


engine = SyncEngine()

delete_count = engine.remove(
    Player, Player.game == "Warzone", just_one=True
)
print(delete_count)
#> 1
