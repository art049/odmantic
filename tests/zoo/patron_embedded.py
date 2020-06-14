from typing import List

from odmantic.model import EmbeddedModel, Model


class Address(EmbeddedModel):
    street: str
    city: str
    state: str
    zip: str


class Patron(Model):
    name: str
    addresses: List[Address]
