from odmantic import Model, query


class Tree(Model):
    name: str
    average_size: float


Tree.name.not_in(["Spruce", "Pine"])
#> QueryExpression({'name': {'$nin': ['Spruce', 'Pine']}})
query.not_in(Tree.name, ["Spruce", "Pine"])
#> QueryExpression({'name': {'$nin': ['Spruce', 'Pine']}})
