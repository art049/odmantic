# Usage with Pydantic

## Defining models with BSON Fields

You might need to define pure Pydantic models which include `BSON` fields. To that end,
you can use the [BaseBSONModel][odmantic.bson.BaseBSONModel] as the base class of your
Pydantic models. This class adds the JSON encoders required to handle the `BSON` fields.

Also, you will have to use the `bson` equivalent types defined in the
[odmantic.bson](api_reference/bson.md) module. Those types, add a validation logic to
the native types from the `bson` module.

!!! note "Custom `json_encoders` with `BaseBSONModel`"
    If you want to specify additional json encoders, with a Pydantic model containing
    `BSON` fields, you will need to pass as well the ODMantic encoders
    ([BSON_TYPES_ENCODERS][odmantic.bson.BSON_TYPES_ENCODERS]).

    ??? example "Custom encoders example"
        ```python linenums="1" hl_lines="11-14 18"
        --8<-- "usage_pydantic/custom_encoders.py"
        ```

    An issue that would simplify this behavior has been opened: [pydantic#2024](https://github.com/samuelcolvin/pydantic/issues/2024){:target=blank_}
## Accessing the underlying pydantic model

Each ODMantic Model contain a pure version of the pydantic model used to build the
ODMantic Model. This Pydantic model can be accessed in the `__pydantic_model__` class
attribute of the ODMantic Model/EmbeddedModel.
