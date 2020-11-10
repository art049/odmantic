from datetime import datetime

from bson import ObjectId

from odmantic import Model
from odmantic.exceptions import DocumentParsingError
from odmantic.field import Field


class User(Model):
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


document = {"name": "Leeroy", "_id": ObjectId("5f8352a87a733b8b18b0cb27")}

try:
    User.parse_doc(document)
except DocumentParsingError as e:
    print(e)
    #> 1 validation error for User
    #> created_at
    #>   key not found in document (type=value_error.keynotfoundindocument; key_name='created_at')
    #> (User instance details: id=ObjectId('5f8352a87a733b8b18b0cb27'))
