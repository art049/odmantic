import pytest
from bson.objectid import ObjectId
from pydantic.error_wrappers import ValidationError

from odmantic.field import Field
from odmantic.model import EmbeddedModel, Model
from tests.zoo.person import PersonModel


def test_repr_model():
    class M(Model):
        a: int

    instance = M(a=5)
    assert repr(instance) == f"M(id={repr(instance.id)}, a=5)"


def test_repr_embedded_model():
    class M(EmbeddedModel):
        a: int

    instance = M(a=5)
    assert repr(instance) == "M(a=5)"


def test_fields_modified_no_modification():
    class M(Model):
        f: int

    instance = M(f=0)
    assert instance.__fields_modified__ == set(["f", "id"])


def test_fields_modified_with_default():
    class M(Model):
        f: int = 5

    instance = M(f=0)
    assert instance.__fields_modified__ == set(["f", "id"])


def test_fields_modified_one_update():
    class M(Model):
        f: int

    instance = M(f=0)
    instance.f = 1
    assert instance.__fields_modified__ == set(["f", "id"])


def test_field_update_with_invalid_data_type():
    class M(Model):
        f: int

    instance = M(f=0)
    with pytest.raises(ValidationError):
        instance.f = "aa"  # type: ignore


def test_field_update_with_invalid_data():
    class M(Model):
        f: int = Field(gt=0)

    instance = M(f=1)
    with pytest.raises(ValidationError):
        instance.f = -1


def test_validate_does_not_copy():
    instance = PersonModel(first_name="Jean", last_name="Pierre")
    assert PersonModel.validate(instance) is instance


def test_validate_from_dict():
    instance = PersonModel.validate({"first_name": "Jean", "last_name": "Pierre"})
    assert isinstance(instance, PersonModel)
    assert instance.first_name == "Jean" and instance.last_name == "Pierre"


def test_fields_modified_on_construction():
    instance = PersonModel(first_name="Jean", last_name="Pierre")
    assert instance.__fields_modified__ == set(["first_name", "last_name", "id"])


def test_fields_modified_on_document_parsing():
    instance = PersonModel.parse_doc(
        {"_id": ObjectId(), "first_name": "Jackie", "last_name": "Chan"}
    )
    assert instance.__fields_modified__ == set(["first_name", "last_name", "id"])


def test_fields_modified_on_object_parsing():
    instance = PersonModel.parse_obj(
        {"_id": ObjectId(), "first_name": "Jackie", "last_name": "Chan"}
    )
    assert instance.__fields_modified__ == set(["first_name", "last_name", "id"])


def test_change_primary_key_value():
    class M(Model):
        ...

    instance = M()
    with pytest.raises(NotImplementedError, match="assigning a new primary key"):
        instance.id = 12


def test_model_copy_not_implemented():
    class M(Model):
        ...

    instance = M()
    with pytest.raises(NotImplementedError):
        instance.copy()


def test_pos_key_name():
    class M(Model):
        field: int = Field(key_name="alternate_name")

    assert +M.field == "alternate_name"
    assert ++M.field == "$alternate_name"
