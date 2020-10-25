from odmantic import AIOEngine, EmbeddedModel, Model
from odmantic.query import desc


class CapitalCity(EmbeddedModel):
    name: str
    population: int


class Country(Model):
    name: str
    currency: str
    capital_city: CapitalCity


engine = AIOEngine()
await engine.find(Country, sort=desc(Country.capital_city.population))
