import json
from datetime import datetime
from typing import Dict

import pytest
from bson import ObjectId
from bson.binary import Binary
from bson.decimal128 import Decimal128
from bson.int64 import Int64
from bson.regex import Regex

from odmantic import Model
from tests.zoo.book_embedded import Book, Publisher
from tests.zoo.full_bson import FullBsonModel
from tests.zoo.patron_embedded import Address, Patron
from tests.zoo.person import PersonModel
from tests.zoo.tree import TreeKind, TreeModel
from tests.zoo.twitter_user import TwitterUser

pytestmark = pytest.mark.asyncio


def test_simple_model_serialization():
    class M(Model): ...

    id_ = ObjectId()
    assert json.loads(M(id=id_).model_dump_json()) == {"id": str(id_)}


TWITTER_USERS = [TwitterUser(), TwitterUser(), TwitterUser()]
MAIN_TWITTER_USER = TwitterUser(following=[e.id for e in TWITTER_USERS])


@pytest.mark.parametrize(
    "instance, expected_parsed_json",
    (
        (
            PersonModel(first_name="Johnny", last_name="Cash"),
            dict(first_name="Johnny", last_name="Cash"),
        ),
        (
            TreeModel(
                name="Secoya",
                average_size=100.3,
                discovery_year=1253,
                kind=TreeKind.BIG,
                genesis_continents=["Asia"],
                per_continent_density={"Asia": 20.3},
            ),
            dict(
                name="Secoya",
                average_size=100.3,
                discovery_year=1253,
                kind="big",
                genesis_continents=["Asia"],
                per_continent_density={"Asia": 20.3},
            ),
        ),
        (
            Book(
                title="Harry Potter",
                pages=550,
                publisher=Publisher(name="A publisher", founded=1995, location="CA"),
            ),
            dict(
                title="Harry Potter",
                pages=550,
                publisher=dict(name="A publisher", founded=1995, location="CA"),
            ),
        ),
        (
            Patron(
                name="Jean Michel",
                addresses=[
                    Address(
                        street="212 Rue de Tolbiac",
                        city="Paris",
                        state="Ile de France",
                        zip="75013",
                    )
                ],
            ),
            dict(
                name="Jean Michel",
                addresses=[
                    dict(
                        street="212 Rue de Tolbiac",
                        city="Paris",
                        state="Ile de France",
                        zip="75013",
                    )
                ],
            ),
        ),
        (MAIN_TWITTER_USER, dict(following=[str(u.id) for u in TWITTER_USERS])),
        (
            FullBsonModel(
                objectId_=ObjectId("5f6bd0f85cac5a450e8eb9e8"),
                long_=Int64(258),
                decimal_=Decimal128("256.123457"),
                # TODO: document some bytes value might be rejected because of utf8
                # encoding: encode in base64 before
                binary_=Binary(b"\x48\x49"),
                regex_=Regex(r"^.*$"),
            ),
            dict(
                objectId_="5f6bd0f85cac5a450e8eb9e8",
                long_=258,
                decimal_="256.123457",
                binary_=b"\x48\x49".decode(),
                regex_=r"^.*$",
            ),
        ),
    ),
)
def test_zoo_serialization_no_id(instance: Model, expected_parsed_json: Dict):
    parsed_data = json.loads(instance.model_dump_json())
    del parsed_data["id"]
    assert parsed_data == expected_parsed_json


@pytest.mark.filterwarnings("ignore:`json_encoders` is deprecated")
def test_custom_json_encoders():
    class M(Model):
        a: datetime = datetime.now()

        model_config = {"json_encoders": {datetime: lambda _: "encoded"}}

    instance = M()
    parsed = json.loads(instance.model_dump_json())
    assert parsed == {"id": str(instance.id), "a": "encoded"}


@pytest.mark.xfail(
    reason=(
        "This doesn't work any more with pydantic v2 since bson fields are "
        "now annotated and take precedence over the custom json encoder."
    )
)
def test_custom_json_encoders_override_builtin_bson():
    class M(Model):
        model_config = {"json_encoders": {ObjectId: lambda _: "encoded"}}

    instance = M()
    parsed = json.loads(instance.model_dump_json())
    assert parsed == {"id": "encoded"}
