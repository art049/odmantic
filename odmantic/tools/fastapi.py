import warnings
from typing import Optional

import fastapi.params
from motor.motor_asyncio import AsyncIOMotorClient

from odmantic.engine import AIOEngine


class AIOEngineDependency(fastapi.params.Depends):
    """AIOEngine FastAPI Dependency.


    Warning:
        Deprecated since v0.2.0, [more
        details](https://art049.github.io/odmantic/usage_fastapi/#building-the-engine).

    Internally caches the AIOEngine instance to avoid creating a new client on each
    request.

    Sample usage:
    ```python
    app = FastAPI()
    EngineD = AIOEngineDependency()

    @app.get("/")
    async def get(engine: AIOEngine = EngineD):
        await engine.find(...)
        await engine.save(...)
    ```

    """

    def __init__(self, mongo_uri: Optional[str] = None, database: str = "test") -> None:
        """Dependency initializer for AIOEngine.

        Args:
            mongo_uri: mongo_uri that should be used for creating the motor client
            database: database to use
        """
        super().__init__(dependency=self)
        self.mongo_uri = mongo_uri
        self.database = database
        self.engine: Optional[AIOEngine] = None
        warnings.warn(
            "the AIOEngineDependency object is deprecated, see "
            "https://art049.github.io/odmantic/usage_fastapi/#building-the-engine "
            "for more details.",
            DeprecationWarning,
        )

    async def __call__(self) -> AIOEngine:
        if self.engine is None:
            motor_client = None
            if self.mongo_uri is not None:
                motor_client = AsyncIOMotorClient(self.mongo_uri)
            self.engine = AIOEngine(motor_client, self.database)
        return self.engine
