from odmantic import AIOEngine, Model


class Player(Model):
    name: str
    game: str


engine = AIOEngine()

delete_count = await engine.delete_many(Player, Player.game == "Warzone")
