from datetime import datetime

from odmantic.bson import BSON_TYPES_ENCODERS, BaseBSONModel, ObjectId


class M(BaseBSONModel):
    id: ObjectId
    date: datetime

    class Config:
        json_encoders = {
            **BSON_TYPES_ENCODERS,
            datetime: lambda dt: dt.year,
        }


print(M(id=ObjectId(), date=datetime.utcnow()).json())
#> {"id": "5fa3378c8fde3766574d874d", "date": 2020}
