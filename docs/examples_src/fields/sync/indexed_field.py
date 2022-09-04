from odmantic import Field, Model, SyncEngine


class Player(Model):
    name: str
    score: int = Field(index=True)


engine = SyncEngine()
engine.configure_database([Player])
