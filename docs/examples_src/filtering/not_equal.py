from odmantic import Model, query


class Tree(Model):
    name: str
    average_size: float


Tree.name != "Spruce"
#> QueryExpression({'name': {'$ne': 'Spruce'}})
Tree.name.ne("Spruce")
#> QueryExpression({'name': {'$ne': 'Spruce'}})
query.ne(Tree.name, "Spruce")
#> QueryExpression({'name': {'$ne': 'Spruce'}})
