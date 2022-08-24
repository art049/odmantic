from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()

player_count = await engine.count(Player)
print(player_count)
#> 4
cs_count = await engine.count(Player, Player.game == "Counter-Strike")
print(cs_count)
#> 1
valorant_count = await engine.count(Player, Player.game == "Valorant")
print(valorant_count)
#> 0
