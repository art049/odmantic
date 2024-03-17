from odmantic.model import Model


class PersonModel(Model):
    model_config = {"collection": "people"}

    first_name: str
    last_name: str
