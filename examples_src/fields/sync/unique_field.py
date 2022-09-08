from odmantic import Field, Model, SyncEngine


class Player(Model):
    name: str = Field(unique=True)


engine = SyncEngine()
engine.configure_database([Player])

leeroy = Player(name="Leeroy")
engine.save(leeroy)

another_leeroy = Player(name="Leeroy")
engine.save(another_leeroy)
#> Raises odmantic.exceptions.DuplicateKeyError:
#>    Duplicate key error for: Player.
#>    Instance: id=ObjectId('6314b4c25a19444bfe0c0be5') name='Leeroy'
