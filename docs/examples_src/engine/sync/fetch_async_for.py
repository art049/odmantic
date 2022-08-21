from odmantic import Model, SyncEngine


class Player(Model):
    name: str
    game: str


engine = SyncEngine()

for player in engine.find(Player, Player.game == "Starcraft"):
    print(repr(player))

#> Player(id=ObjectId(...), name='TLO', game='Starcraft')
#> Player(id=ObjectId(...), name='Serral', game='Starcraft')
