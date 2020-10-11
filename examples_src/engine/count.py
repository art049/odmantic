from odmantic import AIOEngine, Model


class Player(Model):
    name: str


engine = AIOEngine()

player_count = await engine.count(Player)
print(player_count)
#> 4
