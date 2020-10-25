from odmantic import AIOEngine, Model, query

engine = AIOEngine()


class Tree(Model):
    name: str
    average_size: float


# The following queries are equivalent,
# they will sort `Tree` by ascending `average_size`

await engine.find(Tree, sort=Tree.average_size)
await engine.find(Tree, sort=Tree.average_size.asc())
await engine.find(Tree, sort=query.asc(Tree.average_size))
