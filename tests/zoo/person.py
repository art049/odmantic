from odmantic.model import Model


class PersonModel(Model):
    __collection__ = "people"

    first_name: str
    last_name: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
