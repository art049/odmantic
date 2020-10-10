from typing import Tuple

from odmantic import Model


class SimpleTupleModel(Model):
    field: tuple


print(SimpleTupleModel(field=[1, "a", True]).field)
#> (1, 'a', True)
print(SimpleTupleModel(field=(1, "a", True)).field)
#> (1, 'a', True)


class TwoIntTupleModel(Model):
    field: Tuple[int, int]


print(SimpleTupleModel(field=(1, 10)).field)
#> (1, 10)
print(SimpleTupleModel(field=[1, 10]).field)
#> (1, 10)


class IntTupleModel(Model):
    field: Tuple[int, ...]


print(IntTupleModel(field=(1,)).field)
#> (1,)
print(IntTupleModel(field=[1, 2, 3, 10]).field)
#> (1, 2, 3, 10)
