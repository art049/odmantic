from odmantic import Model, query


class Tree(Model):
    name: str
    average_size: float


Tree.name.in_(["Spruce", "Pine"])
#> QueryExpression({'name': {'$in': ['Spruce', 'Pine']}})
query.in_(Tree.name, ["Spruce", "Pine"])
#> QueryExpression({'name': {'$in': ['Spruce', 'Pine']}})
