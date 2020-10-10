from typing import Union

from odmantic import Model


class Thing(Model):
    ref_id: Union[int, str]


thing_1 = Thing(ref_id=42)
print(thing_1.ref_id)
#> 42

thing_2 = Thing(ref_id="i am a string")
print(thing_2.ref_id)
#> i am a string
