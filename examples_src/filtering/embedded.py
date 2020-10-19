from odmantic import AIOEngine, EmbeddedModel, Model


class CapitalCity(EmbeddedModel):
    name: str
    population: int


class Country(Model):
    name: str
    currency: str
    capital_city: CapitalCity


Country.capital_city.name == "Paris"
#> QueryExpression({'capital_city.name': {'$eq': 'Paris'}})
Country.capital_city.population > 10 ** 6
#> QueryExpression({'capital_city.population': {'$gt': 1000000}})
