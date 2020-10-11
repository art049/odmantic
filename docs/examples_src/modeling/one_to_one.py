from odmantic import AIOEngine, EmbeddedModel, Model


class CapitalCity(EmbeddedModel):
    name: str
    population: int


class Country(Model):
    name: str
    currency: str
    capital_city: CapitalCity


countries = [
    Country(
        name="Switzerland",
        currency="Swiss franc",
        capital_city=CapitalCity(name="Bern", population=1035000),
    ),
    Country(
        name="Sweden",
        currency="Swedish krona",
        capital_city=CapitalCity(name="Stockholm", population=975904),
    ),
]

engine = AIOEngine()
await engine.save_all(countries)
