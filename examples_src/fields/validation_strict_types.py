from pydantic import StrictBool, StrictFloat, StrictStr

from odmantic import Model


class ExampleModel(Model):
    strict_bool: StrictBool
    strict_float: StrictFloat
    strict_str: StrictStr
