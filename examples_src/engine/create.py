from odmantic import AIOEngine, Model


class Player(Model):
    name: str


engine = AIOEngine()

leeroy = Player(name="Leeroy Jenkins")
await engine.save(leeroy)

players = [Player(name="xQc"), Player(name="Shroud"), Player(name="Serral")]
await engine.save_all(players)
