from typing import List

from odmantic import AIOEngine, EmbeddedModel, Model


class Address(EmbeddedModel):
    street: str
    city: str
    state: str
    zipcode: str


class Customer(Model):
    name: str
    addresses: List[Address]


customer = Customer(
    name="John Doe",
    addresses=[
        Address(
            street="1757  Birch Street",
            city="Greenwood",
            state="Indiana",
            zipcode="46142",
        ),
        Address(
            street="262  Barnes Avenue",
            city="Cincinnati",
            state="Ohio",
            zipcode="45216",
        ),
    ],
)

engine = AIOEngine()
await engine.save(customer)
