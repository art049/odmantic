# Data types

## Supported BSON types (`bson` package)

- Int64 (long)
- ObjectId (objectId)
- Decimal128 (decimal)

Additionnaly, most of the types supported by pydantic are supported. See [pydantic: Field Types](https://pydantic-docs.helpmanual.io/usage/types) for more details.

## Unsupported types

- typing.Set / set

## Python to BSON type mapping

| Python type            | BSON type  | Comment                                                      |
| ---------------------- | :--------: | ------------------------------------------------------------ |
| `bson.ObjectId`        | `objectId` |
| `bool`                 |   `bool`   |                                                              |
| `int`                  |   `int`    | value between -2^31 and 2^31 - 1                             |
| `int`                  |   `long`   | value not between -2^31 and 2^31 - 1                         |
| `bson.Int64`           |   `long`   |
| `float`                |  `double`  |
| `bson.Decimal128`      | `decimal`  | decimal.Decimal is not supported yet                         |
| `str`                  |  `string`  |
| `typing.Pattern`       |  `regex`   |
| `bson.Regex`           |  `regex`   |
| `bytes`                | `binData`  |
| `bson.Binary`          | `binData`  |
| `datetime.datetime`    |   `date`   | microseconds are truncated, only naive datetimes are allowed |
| `typing.Dict`          |  `object`  |
| `typing.List`          |  `array`   |
| `typing.Sequence`      |  `array`   |
| `typing.Tuple[T, ...]` |  `array`   |
