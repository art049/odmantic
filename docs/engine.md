# Engine

## Creating the engine

=== "AsyncIO"

    ```python
    from motor.motor_asyncio import AsyncIOMotorClient
    from odmantic import AIOEngine

    client = AsyncIOMotorClient("mongodb://localhost:27017/")
    engine = AIOEngine(motor_client=client, db_name="example_db")
    ```

## Create documents

=== "AsyncIO"

    ```python
    class Player(Model):
        name: str

    leeroy = Player(name="Leeroy Jenkins")
    await engine.save(leeroy)
    print(leeroy)
    #> Player(name="Leeroy Jenkins")
    ```

## Count documents

=== "AsyncIO"

    ```python
    count = await engine.count(Player)
    print(count)
    #> 3
    ```

Interop with regular queries link
