from odmantic import Model, query


class Tree(Model):
    name: str
    size: float


(Tree.name == "Spruce") & (Tree.size <= 2)
#> QueryExpression(
#>     {
#>         "$and": (
#>             QueryExpression({"name": {"$eq": "Spruce"}}),
#>             QueryExpression({"size": {"$lte": 2}}),
#>         )
#>     }
#> )
query.and_(Tree.name == "Spruce", Tree.size <= 2)
#> ... same output ...
