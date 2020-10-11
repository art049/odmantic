from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()

players = await engine.find(Player)

for player in players:
    await engine.delete(player)
