from odmantic import AIOEngine, Field, Model


class Player(Model):
    name: str = Field(unique=True)


engine = AIOEngine()
await engine.configure_database([Player])

leeroy = Player(name="Leeroy")
await engine.save(leeroy)

another_leeroy = Player(name="Leeroy")
await engine.save(another_leeroy)
#> Raises odmantic.exceptions.DuplicateKeyError:
#>    Duplicate key error for: Player.
#>    Instance: id=ObjectId('6314b4c25a19444bfe0c0be5') name='Leeroy'
