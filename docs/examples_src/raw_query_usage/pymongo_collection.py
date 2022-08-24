from odmantic import SyncEngine, Model


class User(Model):
    name: str


engine = SyncEngine()
collection = engine.get_collection(User)
print(collection)
#> Collection(
#>     Database(
#>         MongoClient(
#>             host=["localhost:27017"],
#>             document_class=dict,
#>             tz_aware=False,
#>             connect=True,
#>         ),
#>         "test",
#>     ),
#>     "user",
#> )
