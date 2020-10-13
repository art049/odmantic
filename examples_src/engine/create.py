from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()

leeroy = Player(name="Leeroy Jenkins", game="World of Warcraft")
await engine.save(leeroy)

players = [
    Player(name="Shroud", game="Counter-Strike"),
    Player(name="Serral", game="Starcraft"),
    Player(name="TLO", game="Starcraft"),
]
await engine.save_all(players)
