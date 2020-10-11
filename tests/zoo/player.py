from odmantic import Field, Model


class Player(Model):
    """This model has a custom primary key"""

    name: str = Field(primary_field=True)
    level: int = Field(default=1, ge=1)
