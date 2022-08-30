from odmantic import SyncEngine, Model


class Player(Model):
    name: str
    game: str


engine = SyncEngine()

leeroy = Player(name="Leeroy Jenkins", game="World of Warcraft")

with engine.session() as session:
    session.save_all(
        [
            Player(name="Shroud", game="Counter-Strike"),
            Player(name="Serral", game="Starcraft"),
            Player(name="TLO", game="Starcraft"),
        ]
    )
    player_count = session.count(Player)
    print(player_count)
    #> 3
