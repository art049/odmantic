from odmantic.model import Model


class PersonModel(Model):
    class Config:
        collection = "people"

    first_name: str
    last_name: str
