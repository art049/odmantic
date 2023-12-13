from typing import Optional

from odmantic import Model


class Person(Model):
    name: str
    age: Optional[int] = None

john = Person(name="John")
print(john.age)
#> None
