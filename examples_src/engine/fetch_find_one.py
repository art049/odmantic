from odmantic import AIOEngine, Model


class Player(Model):
    name: str


engine = AIOEngine()

player = await engine.find_one(Player)
print(repr(player))
#> Player(id=ObjectId("5f8312ecab747c96fa29f795"), name="Serral"),
