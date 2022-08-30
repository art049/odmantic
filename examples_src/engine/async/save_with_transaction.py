from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()

async with engine.transaction() as transaction:
    await transaction.save(Player(name="Leeroy Jenkins", game="WoW"))
    await transaction.commit()

print(engine.count(Player))
#> 1

async with engine.transaction() as transaction:
    await transaction.save(Player(name="Shroud", game="Counter-Strike"))
    await transaction.save(Player(name="Serral", game="Starcraft"))
    await transaction.abort()

print(engine.count(Player))
#> 1
