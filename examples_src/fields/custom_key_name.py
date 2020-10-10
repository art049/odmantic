from odmantic import AIOEngine, Field, Model


class Player(Model):
    name: str = Field(key_name="username")


engine = AIOEngine()
await engine.save(Player(name="Jack"))
