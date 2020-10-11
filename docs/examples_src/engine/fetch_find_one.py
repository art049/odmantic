from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()

player = await engine.find_one(Player, Player.name == "Serral")
print(repr(player))
#> Player(id=ObjectId(...), name="Serral", game="Starcraft")

another_player = await engine.find_one(
    Player, Player.name == "Player_Not_Stored_In_Database"
)
print(another_player)
#> None
