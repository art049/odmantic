from odmantic import AIOEngine, Model


class Tree(Model):
    name: str
    average_size: float


engine = AIOEngine()
