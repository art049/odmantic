from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()

delete_count = await engine.remove(
    Player, Player.game == "Warzone", just_one=True
)
print(delete_count)
#> 1
