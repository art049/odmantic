from enum import Enum

from odmantic import Model, query


class TreeKind(str, Enum):
    BIG = "big"
    SMALL = "small"


class Tree(Model):
    name: str
    average_size: float
    kind: TreeKind


Tree.kind == TreeKind.SMALL
#> QueryExpression({'kind': {'$eq': 'small'}})
Tree.kind.eq(TreeKind.SMALL)
#> QueryExpression({'kind': {'$eq': 'small'}})
query.eq(Tree.kind, TreeKind.SMALL)
#> QueryExpression({'kind': {'$eq': 'small'}})
