from typing import Dict, Union

from odmantic import Model


class SimpleDictModel(Model):
    field: dict


print(SimpleDictModel(field={18: "a string", True: 42, 18.3: [1, 2, 3]}).field)
#> {18: 'a string', True: 42, 18.3: [1, 2, 3]}


class IntStrDictModel(Model):
    field: Dict[int, str]


print(IntStrDictModel(field={1: "one", 2: "two"}).field)
#> {1: 'one', 2: 'two'}


class IntBoolStrDictModel(Model):
    field: Dict[int, Union[bool, str]]


print(IntBoolStrDictModel(field={0: False, 1: True, 3: "three"}).field)
#> {0: False, 1: True, 3: 'three'}
