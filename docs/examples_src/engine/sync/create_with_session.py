from odmantic import Model, SyncEngine


class Player(Model):
    name: str
    game: str


engine = SyncEngine()

leeroy = Player(name="Leeroy Jenkins", game="World of Warcraft")

with engine.client.start_session() as session:
    engine.save(leeroy, session=session)

players = [
    Player(name="Shroud", game="Counter-Strike"),
    Player(name="Serral", game="Starcraft"),
    Player(name="TLO", game="Starcraft"),
]

with engine.client.start_session() as session:
    engine.save_all(players, session=session)
