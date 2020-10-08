from odmantic import Model


class Player(Model):
    name: str


leeroy = Player(name="Leeroy Jenkins")
print(leeroy.id)
#> ObjectId('5ed50fcad11d1975aa3d7a28')
print(repr(leeroy))
#> Player(id=ObjectId('5ed50fcad11d1975aa3d7a28'), name="Leeroy Jenkins")
