from typing import Dict, List, Optional, Tuple

import pytest
from bson.objectid import ObjectId
from inline_snapshot import snapshot
from pydantic import ValidationError, model_validator, root_validator
from pydantic.main import BaseModel

from odmantic.exceptions import DocumentParsingError
from odmantic.field import Field
from odmantic.model import EmbeddedModel, Model
from odmantic.reference import Reference
from tests.integration.utils import redact_objectid
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


def test_fields_embedded_modified_no_modification():
    class M(EmbeddedModel):
        f: int

    instance = M(f=0)
    assert instance.__fields_modified__ == set(["f"])


def test_fields_modified_with_default():
    class M(Model):
        f: int = 5

    instance = M(f=0)
    assert instance.__fields_modified__ == set(["f", "id"])


@pytest.mark.parametrize("model_cls", [Model, EmbeddedModel])
def test_fields_modified_one_update(model_cls):
    class M(model_cls):  # type: ignore
        f: int

    instance = M(f=0)
    instance.__fields_modified__.clear()
    instance.f = 1
    assert instance.__fields_modified__ == set(["f"])


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
    instance = PersonModel.model_validate_doc(
        {"_id": ObjectId(), "first_name": "Jackie", "last_name": "Chan"}
    )
    assert instance.__fields_modified__ == set(["first_name", "last_name", "id"])


def test_document_parsing_error_keyname():
    class M(Model):
        field: str = Field(key_name="custom")

    id = ObjectId()
    with pytest.raises(DocumentParsingError) as exc_info:
        M.model_validate_doc({"_id": id})
    assert redact_objectid(str(exc_info.value), id) == snapshot(
        """\
1 validation error for M
field
  Key 'custom' not found in document [type=odmantic::key_not_found_in_document, input_value={'_id': ObjectId('<ObjectId>')}, input_type=dict]\
"""  # noqa: E501
    )


def test_document_parsing_error_embedded_keyname():
    class F(EmbeddedModel):
        a: int

    class E(EmbeddedModel):
        f: F

    class M(Model):
        e: E

    with pytest.raises(DocumentParsingError) as exc_info:
        M.model_validate_doc({"_id": ObjectId(), "e": {"f": {}}})
    assert str(exc_info.value) == snapshot(
        """\
1 validation error for M
e.f.a
  Key 'a' not found in document [type=odmantic::key_not_found_in_document, input_value={}, input_type=dict]\
"""  # noqa: E501
    )


def test_embedded_document_parsing_error():
    class E(EmbeddedModel):
        f: int

    with pytest.raises(DocumentParsingError) as exc_info:
        E.model_validate_doc({})
    assert str(exc_info.value) == snapshot(
        """\
1 validation error for E
f
  Key 'f' not found in document [type=odmantic::key_not_found_in_document, input_value={}, input_type=dict]\
"""  # noqa: E501
    )


def test_embedded_document_parsing_validation_error():
    class E(EmbeddedModel):
        f: int

    with pytest.raises(DocumentParsingError) as exc_info:
        E.model_validate_doc({"f": "aa"})
    assert str(exc_info.value).splitlines()[:-1] == snapshot(
        [
            "1 validation error for E",
            "f",
            "  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='aa', input_type=str]",  # noqa: E501
        ]
    )


def test_embedded_model_alternate_key_name_with_default():
    class Em(EmbeddedModel):
        name: str = Field(key_name="username")

    class M(Model):
        f: Em = Em(name="Jack")

    _id = ObjectId()
    doc = {"_id": _id}
    parsed = M.model_validate_doc(doc)
    assert parsed.f.name == "Jack"


def test_embedded_model_alternate_key_name_parsing_exception():
    class Em(EmbeddedModel):
        name: str = Field(key_name="username")

    class M(Model):
        f: Em

    _id = ObjectId()
    doc = {"_id": _id}
    with pytest.raises(DocumentParsingError):
        M.model_validate_doc(doc)


def test_embedded_model_alternate_key_name():
    class Em(EmbeddedModel):
        name: str = Field(key_name="username")

    class M(Model):
        f: Em

    instance = M(f=Em(name="Jack"))
    doc = instance.model_dump_doc()
    assert doc["f"] == {"username": "Jack"}
    parsed = M.model_validate_doc(doc)
    assert parsed == instance


def test_embedded_model_list_alternate_key_name():
    class Em(EmbeddedModel):
        name: str = Field(key_name="username")

    class M(Model):
        f: List[Em]

    instance = M(f=[Em(name="Jack")])
    doc = instance.model_dump_doc()
    assert doc["f"] == [{"username": "Jack"}]
    parsed = M.model_validate_doc(doc)
    assert parsed == instance


def test_embedded_model_tuple_alternate_key_name():
    class Em(EmbeddedModel):
        name: str = Field(key_name="username")

    class M(Model):
        f: Tuple[Em, ...]

    instance = M(f=(Em(name="Jack"),))
    doc = instance.model_dump_doc()
    assert doc["f"] == [{"username": "Jack"}]
    parsed = M.model_validate_doc(doc)
    assert parsed == instance


def test_embedded_model_list_parsing_invalid_type():
    class Em(EmbeddedModel):
        name: str

    class M(Model):
        f: List[Em]

    with pytest.raises(DocumentParsingError) as exc_info:
        M.model_validate_doc({"_id": 1, "f": {1: {"name": "Jack"}}})

    assert str(exc_info.value) == snapshot(
        """\
1 validation error for M
f
  Incorrect generic embedded model value '{1: {'name': 'Jack'}}' [type=odmantic::incorrect_generic_embedded_model_value, input_value={'_id': 1, 'f': {1: {'name': 'Jack'}}}, input_type=dict]\
"""  # noqa: E501
    )


def test_embedded_model_list_parsing_missing_value():
    class Em(EmbeddedModel):
        name: str

    class M(Model):
        f: List[Em]

    with pytest.raises(
        DocumentParsingError,
    ) as exc_info:
        M.model_validate_doc({"_id": 1})
    assert str(exc_info.value) == snapshot(
        """\
1 validation error for M
f
  Key 'f' not found in document [type=odmantic::key_not_found_in_document, input_value={'_id': 1}, input_type=dict]\
"""  # noqa: E501
    )


def test_embedded_model_list_parsing_missing_value_with_default():
    class Em(EmbeddedModel):
        name: str

    class M(Model):
        f: List[Em] = [Em(name="John")]

    parsed = M.model_validate_doc({"_id": ObjectId()})
    assert parsed.f == [Em(name="John")]


def test_embedded_model_dict_parsing_invalid_value():
    class Em(EmbeddedModel):
        name: str

    class M(Model):
        f: Dict[str, Em]

    with pytest.raises(DocumentParsingError) as exc_info:
        M.model_validate_doc({"_id": 1, "f": []})
    assert str(exc_info.value) == snapshot(
        """\
1 validation error for M
f
  Incorrect generic embedded model value '[]' [type=odmantic::incorrect_generic_embedded_model_value, input_value={'_id': 1, 'f': []}, input_type=dict]\
"""  # noqa: E501
    )


def test_embedded_model_dict_parsing_invalid_sub_value():
    class Em(EmbeddedModel):
        e: int

    class M(Model):
        f: Dict[str, Em]

    with pytest.raises(DocumentParsingError) as exc_info:
        M.model_validate_doc({"_id": ObjectId(), "f": {"key": {"not_there": "a"}}})
    assert str(exc_info.value) == snapshot(
        """\
1 validation error for M
f.["key"].e
  Key 'e' not found in document [type=odmantic::key_not_found_in_document, input_value={'not_there': 'a'}, input_type=dict]\
"""  # noqa: E501
    )


def test_embedded_model_list_parsing_invalid_sub_value():
    class Em(EmbeddedModel):
        e: int

    class M(Model):
        f: List[Em]

    with pytest.raises(DocumentParsingError) as exc_info:
        M.model_validate_doc({"_id": ObjectId(), "f": [{"not_there": "a"}]})
    assert str(exc_info.value) == snapshot(
        """\
1 validation error for M
f.[0].e
  Key 'e' not found in document [type=odmantic::key_not_found_in_document, input_value={'not_there': 'a'}, input_type=dict]\
"""  # noqa: E501
    )


def test_fields_modified_on_object_parsing():
    instance = PersonModel.model_validate(
        {"_id": ObjectId(), "first_name": "Jackie", "last_name": "Chan"}
    )
    assert instance.__fields_modified__ == set(["first_name", "last_name", "id"])


def test_change_primary_key_value():
    class M(Model): ...

    instance = M()
    with pytest.raises(NotImplementedError, match="assigning a new primary key"):
        instance.id = 12


def test_model_copy_without_update():
    instance = PersonModel(first_name="Jean", last_name="Valjean")
    copied = instance.model_copy()
    assert instance == copied


def test_model_copy_with_update():
    instance = PersonModel(first_name="Jean", last_name="Valjean")
    copied = instance.model_copy(update={"last_name": "Pierre"})
    assert instance.id == copied.id
    assert instance.first_name == copied.first_name
    assert copied.last_name == "Pierre"


def test_model_copy_with_update_primary_key():
    instance = PersonModel(first_name="Jean", last_name="Valjean")
    copied = instance.model_copy(update={"id": ObjectId()})
    assert instance.first_name == copied.first_name
    assert copied.last_name == copied.last_name
    assert instance.id != copied.id


@pytest.mark.filterwarnings("ignore:copy is deprecated")
def test_deprecated_model_copy_call():
    class M(Model): ...

    with pytest.raises(NotImplementedError):
        M().copy(include={"id"})

    with pytest.raises(NotImplementedError):
        M().copy(exclude={"id"})


def test_model_copy_deep_embedded():
    class E(EmbeddedModel):
        f: int

    class M(Model):
        e: E

    instance = M(e=E(f=1))
    copied = instance.model_copy(deep=True)
    assert instance.e is not copied.e


def test_model_copy_deep_embedded_mutability():
    class F(EmbeddedModel):
        g: int

    class E(EmbeddedModel):
        f: F

    class M(Model):
        e: E

    instance = M(e=E(f=F(g=1)))
    copied = instance.model_copy(deep=True)
    copied.e.f.g = 42
    assert instance.e.f.g != copied.e.f.g


def test_model_copy_not_deep_embedded():
    class E(EmbeddedModel):
        f: int

    class M(Model):
        e: E

    instance = M(e=E(f=1))
    copied = instance.model_copy(deep=False)
    assert instance.e is copied.e


@pytest.mark.parametrize("deep", [True, False])
def test_model_copy_with_reference(deep: bool):
    class R(Model):
        f: int

    class M(Model):
        r: R = Reference()

    ref_instance = R(f=12)
    instance = M(r=ref_instance)
    copied = instance.model_copy(deep=deep)
    assert instance.model_dump_doc() == copied.model_dump_doc()
    assert instance.r == copied.r


@pytest.mark.parametrize("deep", [True, False])
def test_model_copy_field_modified(deep: bool):
    class M(Model):
        f: int

    instance = M(f=5)
    object.__setattr__(instance, "__fields_modified__", set())
    copied = instance.model_copy(update={"f": 12}, deep=deep)
    assert "f" in copied.__fields_modified__


@pytest.mark.parametrize("deep", [True, False])
def test_model_copy_field_modified_on_primary_field_change(deep: bool):
    class M(Model):
        f0: int
        f1: int
        f2: int

    instance = M(f0=12, f1=5, f2=6)
    object.__setattr__(instance, "__fields_modified__", set())
    copied = instance.model_copy(deep=deep)
    assert {"id", "f0", "f1", "f2"} == copied.__fields_modified__


INITIAL_FIRST_NAME, INITIAL_LAST_NAME = "INITIAL_FIRST_NAME", "INITIAL_LAST_NAME"
UPDATED_NAME = "UPDATED_NAME"


@pytest.fixture
def instance_to_update():
    return PersonModel(first_name=INITIAL_FIRST_NAME, last_name=INITIAL_LAST_NAME)


def test_update_pydantic_model(instance_to_update):
    class Update(BaseModel):
        first_name: str

    update_obj = Update(first_name=UPDATED_NAME)
    instance_to_update.model_update(update_obj)
    assert instance_to_update.first_name == UPDATED_NAME
    assert instance_to_update.last_name == INITIAL_LAST_NAME


def test_update_dictionary(instance_to_update):
    update_obj = {"first_name": UPDATED_NAME}
    instance_to_update.model_update(update_obj)
    assert instance_to_update.first_name == UPDATED_NAME
    assert instance_to_update.last_name == INITIAL_LAST_NAME


def test_update_include(instance_to_update):
    update_obj = {"first_name": UPDATED_NAME}
    instance_to_update.model_update(update_obj, include=set())
    assert instance_to_update.first_name == INITIAL_FIRST_NAME
    assert instance_to_update.last_name == INITIAL_LAST_NAME


def test_update_exclude(instance_to_update):
    update_obj = {"first_name": UPDATED_NAME}
    instance_to_update.model_update(update_obj, exclude={"first_name"})
    assert instance_to_update.first_name == INITIAL_FIRST_NAME
    assert instance_to_update.last_name == INITIAL_LAST_NAME


def test_update_exclude_none(instance_to_update):
    class Update(BaseModel):
        first_name: Optional[str]
        last_name: Optional[str]

    update_obj = Update(first_name=UPDATED_NAME, last_name=None)
    instance_to_update.model_update(update_obj, exclude_unset=False, exclude_none=True)
    assert instance_to_update.first_name == UPDATED_NAME
    assert instance_to_update.last_name == INITIAL_LAST_NAME


def test_update_exclude_defaults(instance_to_update):
    initial_instance = instance_to_update.model_copy()

    class Update(BaseModel):
        first_name: Optional[str] = None
        last_name: str = UPDATED_NAME

    update_obj = Update()
    instance_to_update.model_update(
        update_obj, exclude_unset=False, exclude_defaults=True
    )
    assert instance_to_update == initial_instance


def test_update_exclude_over_include(instance_to_update):
    update_obj = {"first_name": UPDATED_NAME}
    instance_to_update.model_update(
        update_obj, include={"first_name"}, exclude={"first_name"}
    )
    assert instance_to_update.first_name == INITIAL_FIRST_NAME
    assert instance_to_update.last_name == INITIAL_LAST_NAME


def test_update_invalid():
    class M(Model):
        f: int

    instance = M(f=12)
    update_obj = {"f": "aaa"}
    with pytest.raises(ValidationError):
        instance.model_update(update_obj)


def test_update_model_undue_update_fields():
    class M(Model):
        f: int

    instance = M(f=12)
    update_obj = {"not_in_model": "aaa"}
    instance.model_update(update_obj)


def test_update_pydantic_unset_update_fields():
    UPDATEED_VALUE = 100

    class P(BaseModel):
        f: int = UPDATEED_VALUE

    class M(Model):
        f: int

    instance = M(f=0)
    update_obj = P()
    instance.model_update(update_obj)
    assert instance.f != UPDATEED_VALUE


def test_update_pydantic_unset_update_fields_include_unset():
    UPDATEED_VALUE = 100

    class P(BaseModel):
        f: int = UPDATEED_VALUE

    class M(Model):
        f: int

    instance = M(f=0)
    update_obj = P()
    instance.model_update(update_obj, exclude_unset=False)
    assert instance.f == UPDATEED_VALUE


def test_update_embedded_model():
    class E(EmbeddedModel):
        f: int

    instance = E(f=12)
    instance.model_update({"f": 15})
    assert instance.f == 15


def test_update_reference():
    class R(Model):
        f: int

    class M(Model):
        r: R = Reference()

    r0 = R(f=0)
    r1 = R(f=1)

    instance = M(r=r0)
    instance.model_update({"r": r1})
    assert instance.r.f == r1.f
    assert instance.r == r1


def test_update_type_coercion():
    class M(Model):
        f: int

    instance = M(f=12)
    update_obj = {"f": "12"}
    instance.model_update(update_obj)
    assert isinstance(instance.f, int)


def test_update_side_effect_field_modified():
    class Rectangle(Model):
        width: float
        height: float
        area: float = 0

        @model_validator(mode="before")
        def set_area(cls, v):
            v["area"] = v["width"] * v["height"]
            return v

    r = Rectangle(width=1, height=1)
    assert r.area == 1
    r.__fields_modified__.clear()
    r.model_update({"width": 5})
    assert r.area == 5
    assert "area" in r.__fields_modified__


@pytest.mark.filterwarnings(
    "ignore: Pydantic V1 style `@root_validator` validators are deprecated"
)
def test_update_side_effect_field_modified_with_root_validator():
    class Rectangle(Model):
        width: float
        height: float
        area: float = 0

        @root_validator(skip_on_failure=True)
        def set_area(cls, v):
            v["area"] = v["width"] * v["height"]
            return v

    r = Rectangle(width=1, height=1)
    assert r.area == 1
    r.__fields_modified__.clear()
    r.model_update({"width": 5})
    assert r.area == 5
    assert "area" in r.__fields_modified__


def test_update_dict_id_exception():
    class M(Model):
        alternate_id: int = Field(primary_field=True)
        f: int

    m = M(alternate_id=0, f=0)
    with pytest.raises(ValueError, match="Updating the primary key is not supported"):
        m.model_update({"alternate_id": 1})


@pytest.mark.parametrize(
    "update_kwargs",
    (
        {"include": set()},
        {"exclude": {"alternate_id"}},
        {"include": {"alternate_id"}, "exclude": {"alternate_id"}},
    ),
)
def test_update_dict_alternate_id_filtered(update_kwargs):
    class M(Model):
        alternate_id: int = Field(primary_field=True)
        f: int

    m = M(alternate_id=0, f=0)
    m.model_update({"alternate_id": 1}, **update_kwargs)
    assert m.f == 0 and m.alternate_id == 0, "instance should be unchanged"


def test_update_pydantic_id_exception():
    class M(Model):
        alternate_id: int = Field(primary_field=True)
        f: int

    m = M(alternate_id=0, f=0)

    class UpdateObject(BaseModel):
        alternate_id: int

    with pytest.raises(ValueError, match="Updating the primary key is not supported"):
        m.model_update(UpdateObject(alternate_id=1))


@pytest.mark.parametrize(
    "update_kwargs",
    (
        {"include": set()},
        {"exclude": {"alternate_id"}},
        {"include": {"alternate_id"}, "exclude": {"alternate_id"}},
    ),
)
def test_update_pydantic_alternate_id_filtered(update_kwargs):
    class M(Model):
        alternate_id: int = Field(primary_field=True)
        f: int

    class UpdateObject(BaseModel):
        alternate_id: int

    m = M(alternate_id=0, f=0)
    m.model_update(UpdateObject(alternate_id=1), **update_kwargs)
    assert m.f == 0 and m.alternate_id == 0, "instance should be unchanged"
