from odmantic import Model, query


class Tree(Model):
    name: str


Tree.name.match(r"^Spruce")
#> QueryExpression({'name': re.compile('^Spruce')})
query.match(Tree.name, r"^Spruce")
#> QueryExpression({'name': re.compile('^Spruce')})
