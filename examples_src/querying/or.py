from odmantic import Model, query


class Tree(Model):
    name: str
    size: float


(Tree.name == "Spruce") | (Tree.size > 2)
#> QueryExpression(
#>     {
#>         "$or": (
#>             QueryExpression({"name": {"$eq": "Spruce"}}),
#>             QueryExpression({"size": {"$gt": 2}}),
#>         )
#>     }
#> )
query.or_(Tree.name == "Spruce", Tree.size > 2)
#> ... same output ...
