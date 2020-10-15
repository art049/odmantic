from odmantic import Model, query


class Tree(Model):
    name: str
    average_size: float


Tree.average_size < 2
#> QueryExpression({'average_size': {'$lt': 2}})
Tree.average_size.lt(2)
#> QueryExpression({'average_size': {'$lt': 2}})
query.lt(Tree.average_size, 2)
#> QueryExpression({'average_size': {'$lt': 2}})

Tree.average_size <= 2
#> QueryExpression({'average_size': {'$lte': 2}})
Tree.average_size.lte(2)
#> QueryExpression({'average_size': {'$lte': 2}})
query.lte(Tree.average_size, 2)
#> QueryExpression({'average_size': {'$lte': 2}})
