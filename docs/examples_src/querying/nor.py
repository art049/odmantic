from odmantic import Model, query


class Tree(Model):
    name: str
    size: float


query.nor_(Tree.name == "Spruce", Tree.size > 2)
# > QueryExpression(
# >     {
# >         "$nor": (
# >             QueryExpression({"name": {"$eq": "Spruce"}}),
# >             QueryExpression({"size": {"$gt": 2}}),
# >         )
# >     }
# > )
