import enum
from typing import Dict, List

from odmantic.field import Field
from odmantic.model import Model


class TreeKind(str, enum.Enum):
    BIG = "big"
    SMALL = "small"


class TreeModel(Model):
    name: str = Field(default="Acacia des montagnes")
    average_size: float = Field(key_name="size")
    discovery_year: int
    kind: TreeKind
    genesis_continents: List[str]
    per_continent_density: Dict[str, float]
