from enum import Enum, auto


class Color(Enum):
    RED = auto()
    BLUE = auto()


print(Color.RED.value)
#> 1
print(Color.BLUE.value)
#> 2
