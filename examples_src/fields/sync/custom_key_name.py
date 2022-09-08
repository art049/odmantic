from odmantic import SyncEngine, Field, Model


class Player(Model):
    name: str = Field(key_name="username")


engine = SyncEngine()
engine.save(Player(name="Jack"))
