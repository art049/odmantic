from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()

leeroy = Player(name="Leeroy Jenkins", game="World of Warcraft")

async with await engine.client.start_session() as session:
    async with session.start_transaction():
        await engine.save(leeroy, session=session)

players = [
    Player(name="Shroud", game="Counter-Strike"),
    Player(name="Serral", game="Starcraft"),
    Player(name="TLO", game="Starcraft"),
]

async with await engine.client.start_session() as session:
    async with session.start_transaction():
        await engine.save_all(players, session=session)
