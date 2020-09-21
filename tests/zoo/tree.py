import enum
from typing import Dict, List

from odmantic.field import Field
from odmantic.model import Model


class TreeKind(str, enum.Enum):
    BIG = "big"
    SMALL = "small"


class TreeModel(Model):
    name: str = Field(primary_key=True, default="Acacia des montagnes")
    average_size: float = Field(mongo_name="size")
    discovery_year: int
    kind: TreeKind
    genesis_continents: List[str]
    per_continent_density: Dict[str, float]
