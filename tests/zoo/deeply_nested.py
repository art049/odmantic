from odmantic.model import Model
from odmantic.reference import Reference


class NestedLevel3(Model):
    field: int = 3


class NestedLevel2(Model):
    field: int = 2
    next_: NestedLevel3 = Reference()


class NestedLevel1(Model):
    field: int = 1
    next_: NestedLevel2 = Reference()
