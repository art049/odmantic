from odmantic import Field, Model


class Player(Model):
    name: str
    level: int = Field(default=1, ge=1)


p = Player(name="Dash")
print(repr(p))
#> Player(id=ObjectId('5f7cdbfbb54a94e9e8717c77'), name='Dash', level=1)
