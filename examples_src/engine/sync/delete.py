from odmantic import SyncEngine, Model


class Player(Model):
    name: str
    game: str


engine = SyncEngine()

players = engine.find(Player)

for player in players:
    engine.delete(player)
