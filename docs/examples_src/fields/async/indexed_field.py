from odmantic import AIOEngine, Field, Model


class Player(Model):
    name: str
    score: int = Field(index=True)


engine = AIOEngine()
await engine.configure_database([Player])
