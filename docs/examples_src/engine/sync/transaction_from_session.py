from odmantic import Model, SyncEngine


class Player(Model):
    name: str
    game: str


engine = SyncEngine()

with engine.session() as session:
    leeroy = session.save(Player(name="Leeroy Jenkins", game="WoW"))
    shroud = session.save(Player(name="Shroud", game="Counter-Strike"))
    with session.transaction() as transaction:
        leeroy.game = "Fortnite"
        transaction.save(leeroy)
        shroud.game = "Fortnite"
        transaction.save(shroud)
        transaction.commit()

print(engine.count(Player, Player.game == "Fortnite"))
#> 2
