from odmantic import SyncEngine, Model


class Player(Model):
    name: str
    game: str


engine = SyncEngine()

leeroy = Player(name="Leeroy Jenkins", game="World of Warcraft")
engine.save(leeroy)

players = [
    Player(name="Shroud", game="Counter-Strike"),
    Player(name="Serral", game="Starcraft"),
    Player(name="TLO", game="Starcraft"),
]
engine.save_all(players)
