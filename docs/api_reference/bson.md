This module provides helpers to build Pydantic Models containing BSON objects.

## Pydantic model helpers

::: odmantic.bson.BaseBSONModel
    selection:
        members:
          -

::: odmantic.bson.BSON_TYPES_ENCODERS

Encoders required to encode BSON fields (can be used in the Pydantic Model's `Config.json_encoders` parameter). See [pydantic: JSON Encoders](https://pydantic-docs.helpmanual.io/usage/exporting_models/#json_encoders){:target=blank_} for more details.

## Pydantic type helpers

Those helpers inherit directly from their respective `bson` types. They add the field
validation logic required by Pydantic to work with them. On top of this, the appropriate JSON schemas are generated for them.

::: odmantic.bson.ObjectId
::: odmantic.bson.Int64
::: odmantic.bson.Decimal128
::: odmantic.bson.Binary
::: odmantic.bson.Regex
