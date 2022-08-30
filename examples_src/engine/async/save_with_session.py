from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()

leeroy = Player(name="Leeroy Jenkins", game="World of Warcraft")

async with engine.session() as session:
    await session.save_all(
        [
            Player(name="Shroud", game="Counter-Strike"),
            Player(name="Serral", game="Starcraft"),
            Player(name="TLO", game="Starcraft"),
        ]
    )
    player_count = await session.count(Player)
    print(player_count)
    #> 3
