import importlib.metadata

from .bson import ObjectId, WithBsonSerializer
from .engine import AIOEngine, SyncEngine
from .field import Field
from .index import Index
from .model import EmbeddedModel, Model
from .reference import Reference

__all__ = [
    "AIOEngine",
    "Model",
    "EmbeddedModel",
    "Field",
    "Reference",
    "Index",
    "ObjectId",
    "SyncEngine",
    "WithBsonSerializer",
]


__version__ = importlib.metadata.version(__name__)
