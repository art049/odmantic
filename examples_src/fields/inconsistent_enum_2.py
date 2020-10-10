from enum import Enum, auto


class Color(Enum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()


print(Color.RED.value)
#> 1
print(Color.GREEN.value)
#> 2
print(Color.BLUE.value)
#> 3
