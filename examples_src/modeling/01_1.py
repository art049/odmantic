await engine.find_one(
    Country, Country.capital_city.name == "Stockholm"
)
#> Country(
#>     id=ObjectId("5f79d7e8b305f24ca43593e2"),
#>     name="Sweden",
#>     currency="Swedish krona",
#>     capital_city=CapitalCity(name="Stockholm", population=975904),
#> )
