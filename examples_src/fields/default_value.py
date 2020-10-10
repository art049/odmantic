from odmantic import Model


class Player(Model):
    name: str
    level: int = 0


p = Player(name="Dash")
print(repr(p))
#> Player(id=ObjectId('5f7cd4be16af832772f1615e'), name='Dash', level=0)
