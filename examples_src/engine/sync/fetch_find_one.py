from odmantic import Model, SyncEngine


class Player(Model):
    name: str
    game: str


engine = SyncEngine()

player = engine.find_one(Player, Player.name == "Serral")
print(repr(player))
#> Player(id=ObjectId(...), name="Serral", game="Starcraft")

another_player = engine.find_one(
    Player, Player.name == "Player_Not_Stored_In_Database"
)
print(another_player)
#> None
