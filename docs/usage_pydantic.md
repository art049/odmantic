# Usage with Pydantic

## Defining models with BSON Fields

You might need to define pure Pydantic models which include `BSON` fields. To that end,
you can use the [BaseBSONModel][odmantic.bson.BaseBSONModel] as the base class of your
Pydantic models. This class adds the JSON encoders required to handle the `BSON` fields.

Also, you will have to use the `bson` equivalent types defined in the
[odmantic.bson](api_reference/bson.md) module. Those types, add a validation logic to
the native types from the `bson` module.

## Accessing the underlying pydantic model

Each ODMantic Model contain a pure version of the pydantic model used to build the
ODMantic Model. This Pydantic model can be accessed in the `__pydantic_model__` class
attribute of the ODMantic Model/EmbeddedModel.
