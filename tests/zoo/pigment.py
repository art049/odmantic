from typing import Set

from odmantic import Model


class Pigment(Model):
    colors: Set[str]
