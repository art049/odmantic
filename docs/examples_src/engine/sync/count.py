from odmantic import Model, SyncEngine


class Player(Model):
    name: str
    game: str


engine = SyncEngine()

player_count = engine.count(Player)
print(player_count)
#> 4
cs_count = engine.count(Player, Player.game == "Counter-Strike")
print(cs_count)
#> 1
valorant_count = engine.count(Player, Player.game == "Valorant")
print(valorant_count)
#> 0
