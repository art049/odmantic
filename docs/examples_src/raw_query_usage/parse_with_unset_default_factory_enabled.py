from datetime import datetime

from bson import ObjectId

from odmantic import Model
from odmantic.exceptions import DocumentParsingError
from odmantic.field import Field


class User(Model):
    name: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"parse_doc_with_default_factories": True}


document = {"name": "Leeroy", "_id": ObjectId("5f8352a87a733b8b18b0cb27")}

user = User.model_validate_doc(document)
print(repr(user))
#> User(
#>     id=ObjectId("5f8352a87a733b8b18b0cb27"),
#>     name="Leeroy",
#>     updated_at=datetime.datetime(2020, 11, 8, 23, 28, 19, 980000),
#> )
