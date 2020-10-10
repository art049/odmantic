from odmantic import AIOEngine, Field, Model


class Player(Model):
    name: str = Field(primary_field=True)


leeroy = Player(name="Leeroy Jenkins")
print(repr(leeroy))
#> Player(name="Leeroy Jenkins")

engine = AIOEngine()
await engine.save(leeroy)
