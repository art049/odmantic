# Data types

## Supported BSON types

- Int64 (long)
- ObjectId (objectId)
- Decimal128 (decimal)

Additionnaly, all types supported by pydantic are supported. See [pydantic: Field Types](https://pydantic-docs.helpmanual.io/usage/types) for more details.

## Python to BSON type mapping

| Python type                | BSON type |
| -------------------------- | :-------: |
| bson.ObjectId              | objectId  |
| bool                       |   bool    |
| int                        |    int    |
| int (greater than 2^32)    |   long    |
| bson.int64.Int64           |   long    |
| float                      |  double   |
| bson.decimal128.Decimal128 |  decimal  |
| str                        |  string   |
| typing.Pattern             |   regex   |
| bytes                      |  binData  |
| bson.binary.Binary         |  binData  |
| datetime.datetime          |   date    |
| typing.Dict                |  object   |
| typing.List                |   array   |
| typing.Sequence            |   array   |
| typing.Tuple[T, ...]       |   array   |
