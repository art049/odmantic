from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()

async with engine.session() as session:
    leeroy = await session.save(Player(name="Leeroy Jenkins", game="WoW"))
    shroud = await session.save(Player(name="Shroud", game="Counter-Strike"))
    async with session.transaction() as transaction:
        leeroy.game = "Fortnite"
        await transaction.save(leeroy)
        shroud.game = "Fortnite"
        await transaction.save(shroud)
        await transaction.commit()

print(await engine.count(Player, Player.game == "Fortnite"))
#> 2
