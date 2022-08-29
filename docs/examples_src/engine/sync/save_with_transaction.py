from odmantic import Model, SyncEngine


class Player(Model):
    name: str
    game: str


engine = SyncEngine()

with engine.transaction() as transaction:
    transaction.save(Player(name="Leeroy Jenkins", game="WoW"))
    transaction.commit()

print(engine.count(Player))
#> 1

with engine.transaction() as transaction:
    transaction.save(Player(name="Shroud", game="Counter-Strike"))
    transaction.save(Player(name="Serral", game="Starcraft"))
    transaction.abort()

print(engine.count(Player))
#> 1
