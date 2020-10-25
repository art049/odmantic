from odmantic import AIOEngine, Model, query

engine = AIOEngine()


class Tree(Model):
    name: str
    average_size: float


# This query will first sort on ascending `average_size`, then
# on descending `name` when `average_size` is the same

await engine.find(Tree, sort=(Tree.average_size, Tree.name.desc()))
