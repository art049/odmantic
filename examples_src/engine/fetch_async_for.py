from odmantic import AIOEngine, Model


class Player(Model):
    name: str


engine = AIOEngine()

async for player in engine.find(Player):
    print(repr(player))

#> Player(id=ObjectId('5f8312ecab747c96fa29f792'), name='Leeroy Jenkins')
#> Player(id=ObjectId('5f8312ecab747c96fa29f793'), name='xQc')
#> Player(id=ObjectId('5f8312ecab747c96fa29f794'), name='Shroud')
#> Player(id=ObjectId('5f8312ecab747c96fa29f795'), name='Serral')
