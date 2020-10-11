from odmantic import AIOEngine, Model


class User(Model):
    name: str


engine = AIOEngine()
motor_collection = engine.get_collection(User)
print(motor_collection)
#> AsyncIOMotorCollection(
#>     Collection(
#>         Database(
#>             MongoClient(
#>                 host=["localhost:27017"],
#>                 document_class=dict,
#>                 tz_aware=False,
#>                 connect=False,
#>                 driver=DriverInfo(name="Motor", version="2.2.0", platform="asyncio"),
#>             ),
#>             "test",
#>         ),
#>         "user",
#>     )
#> )
