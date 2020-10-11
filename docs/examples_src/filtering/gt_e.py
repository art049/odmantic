from odmantic import Model, query


class Tree(Model):
    name: str
    average_size: float


Tree.average_size > 2
#> QueryExpression({'average_size': {'$gt': 2}})
Tree.average_size.gt(2)
#> QueryExpression({'average_size': {'$gt': 2}})
query.gt(Tree.average_size, 2)
#> QueryExpression({'average_size': {'$gt': 2}})

Tree.average_size >= 2
#> QueryExpression({'average_size': {'$gte': 2}})
Tree.average_size.gte(2)
#> QueryExpression({'average_size': {'$gte': 2}})
query.gte(Tree.average_size, 2)
#> QueryExpression({'average_size': {'$gte': 2}})
