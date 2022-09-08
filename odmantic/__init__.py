from .bson import ObjectId
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
]

# Cleanest way to handle version changes with poetry while not hardcoding the version
# https://github.com/python-poetry/poetry/pull/2366#issuecomment-652418094
try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    import importlib_metadata  # type: ignore

__version__ = importlib_metadata.version(__name__)
