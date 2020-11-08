import pytest
from bson.objectid import ObjectId
from pydantic.error_wrappers import ValidationError

from odmantic.exceptions import DocumentParsingError
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


def test_document_parsing_error_keyname():
    class M(Model):
        field: str = Field(key_name="custom")

    id = ObjectId()
    with pytest.raises(DocumentParsingError) as exc_info:
        M.parse_doc({"_id": id})
    assert str(exc_info.value) == (
        "1 validation error for M\n"
        "field\n"
        "  key not found in document "
        "(type=value_error.keynotfoundindocument; key_name='custom')\n"
        f"(M instance details: id={repr(id)})"
    )


def test_document_parsing_error_embedded_keyname():
    class F(EmbeddedModel):
        a: int

    class E(EmbeddedModel):
        f: F

    class M(Model):
        e: E

    with pytest.raises(DocumentParsingError) as exc_info:
        M.parse_doc({"_id": ObjectId(), "e": {"f": {}}})
    assert (
        "1 validation error for M\n"
        "e -> f -> a\n"
        "  field required (type=value_error.missing)"
    ) in str(exc_info.value)


def test_embedded_document_parsing_error():
    class E(EmbeddedModel):
        f: int

    with pytest.raises(DocumentParsingError) as exc_info:
        E.parse_doc({})
    assert str(exc_info.value) == (
        "1 validation error for E\n"
        "f\n"
        "  key not found in document "
        "(type=value_error.keynotfoundindocument; key_name='f')"
    )


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
