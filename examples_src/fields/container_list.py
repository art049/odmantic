from typing import List, Union

from odmantic import Model


class SimpleListModel(Model):
    field: list


print(SimpleListModel(field=[1, "a", True]).field)
#> [1, 'a', True]
print(SimpleListModel(field=(1, "a", True)).field)
#> [1, 'a', True]


class IntListModel(Model):
    field: List[int]


print(IntListModel(field=[1, 5]).field)
#> [1, 5]
print(IntListModel(field=(1, 5)).field)
#> [1, 5]


class IntStrListModel(Model):
    field: List[Union[int, str]]


print(IntStrListModel(field=[1, "b"]).field)
#> [1, 'b']
print(IntStrListModel(field=(1, "b")).field)
#> [1, 'b']
