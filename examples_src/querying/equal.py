from odmantic import Model, query


class Tree(Model):
    name: str
    average_size: float


Tree.name == "Spruce"
#> QueryExpression({'name': {'$eq': 'Spruce'}})
Tree.name.eq("Spruce")
#> QueryExpression({'name': {'$eq': 'Spruce'}})
query.eq(Tree.name, "Spruce")
#> QueryExpression({'name': {'$eq': 'Spruce'}})
