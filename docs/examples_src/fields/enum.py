from enum import Enum

from odmantic import AIOEngine, Model


class TreeKind(str, Enum):
    BIG = "big"
    SMALL = "small"


class Tree(Model):
    name: str
    kind: TreeKind


sequoia = Tree(name="Sequoia", kind=TreeKind.BIG)
print(sequoia.kind)
#> TreeKind.BIG
print(sequoia.kind == "big")
#> True

spruce = Tree(name="Spruce", kind="small")
print(spruce.kind)
#> TreeKind.SMALL
print(spruce.kind == TreeKind.SMALL)
#> True

engine = AIOEngine()
await engine.save_all([sequoia, spruce])
