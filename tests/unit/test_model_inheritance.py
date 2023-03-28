import sys
from typing import Any, Dict, List, Union

import pytest

from odmantic.field import Field
from odmantic.model import EmbeddedModel, Model
from odmantic.reference import Reference

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated


def get_child_model(base_model):
    class CustomFloat(float):
        @classmethod
        def __bson__(cls, v):
            return str(v)

        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def validate(cls, v):
            return float(v)

    class Referenced(Model):
        a: int

    class Parent(base_model):  # type: ignore
        p_req: str
        p_bson: CustomFloat
        p_mut: Dict[str, Any] = Field(default_factory=dict)
        p_ref: Referenced = Reference()

        class Config:
            title = "Parent"
            anystr_strip_whitespace = True

    class Child(Parent):
        c_req: int
        c_bson: CustomFloat
        c_mut: List[str] = Field(default_factory=list)
        c_ref: Referenced = Reference()

        class Config:
            collection = "children"
            title = "Child"

    return Child


@pytest.mark.parametrize("base_model", [Model, EmbeddedModel])
def test_model_inherited_field(base_model):
    Child = get_child_model(base_model)
    expected_fields = [
        "p_req",
        "p_bson",
        "p_mut",
        "p_ref",
        "id",
        "c_req",
        "c_bson",
        "c_mut",
        "c_ref",
    ]
    if base_model is EmbeddedModel:
        expected_fields.remove("id")
    assert list(Child.__fields__.keys()) == expected_fields


@pytest.mark.parametrize("base_model", [Model, EmbeddedModel])
def test_model_inherited_bson_serialized_fields(base_model):
    Child = get_child_model(base_model)
    assert Child.__bson_serialized_fields__ == frozenset({"p_bson", "c_bson"})


@pytest.mark.parametrize("base_model", [Model, EmbeddedModel])
def test_model_inherited_mutable(base_model):
    Child = get_child_model(base_model)
    assert Child.__mutable_fields__ == frozenset({"p_mut", "c_mut"})


@pytest.mark.parametrize("base_model", [Model, EmbeddedModel])
def test_model_inherited_refs(base_model):
    Child = get_child_model(base_model)
    assert Child.__references__ == ("p_ref", "c_ref")


@pytest.mark.parametrize("base_model", [Model, EmbeddedModel])
def test_model_inherited_config(base_model):
    Child = get_child_model(base_model)
    assert Child.Config.anystr_strip_whitespace is True
    assert Child.Config.collection == "children"
    assert Child.Config.title == "Child"


def test_polymorphic_model():
    class Shape(Model):
        area: float
        perimeter: float

        class Config:
            collection = "shapes"

    class Circle(Shape):
        type: str = Field("circle", const=True)
        radius: float

    class Rectangle(Shape):
        type: str = Field("rectangle", const=True)
        width: float
        height: float

    class Table(EmbeddedModel):
        material: str
        shape: Shape = Reference()

    tables = [
        Table(material="steel", shape=Circle(area=3.14, perimeter=6.28, radius=1)),
        Table(material="oak", shape=Rectangle(area=2, perimeter=6, width=1, height=2)),
    ]
    docs = [
        {"material": "steel", "shape": tables[0].shape.id},
        {"material": "oak", "shape": tables[1].shape.id},
    ]
    for table, doc in zip(tables, docs):
        assert table.doc() == doc

        # parse_doc expects the embedded documents, not references
        doc["shape"] = table.shape.doc()
        parsed_table = Table.parse_doc(doc)
        assert parsed_table.material == table.material
        # parsed_table.shape is an "upcasted" Shape instance of the original shape
        assert parsed_table.shape == Shape(**table.shape.dict())


@pytest.mark.parametrize("discriminating_union", [False, True])
def test_polymorphic_embedded_model(discriminating_union):
    class Shape(EmbeddedModel):
        area: float
        perimeter: float

    class Circle(Shape):
        type: str = Field("circle", const=True)
        radius: float

    class Rectangle(Shape):
        type: str = Field("rectangle", const=True)
        width: float
        height: float

    class Table(EmbeddedModel):
        material: str
        if discriminating_union:
            shape: Annotated[Union[Circle, Rectangle], Field(discriminator="type")]
        else:
            shape: Shape  # type: ignore[no-redef]

    tables = [
        Table(material="steel", shape=Circle(area=3.14, perimeter=6.28, radius=1)),
        Table(material="oak", shape=Rectangle(area=2, perimeter=6, width=1, height=2)),
    ]
    docs = [
        {
            "material": "steel",
            "shape": {
                "type": "circle",
                "radius": 1.0,
                "area": 3.14,
                "perimeter": 6.28,
            },
        },
        {
            "material": "oak",
            "shape": {
                "type": "rectangle",
                "width": 1.0,
                "height": 2.0,
                "area": 2.0,
                "perimeter": 6.0,
            },
        },
    ]
    for table, doc in zip(tables, docs):
        assert table.doc() == doc

        parsed_table = Table.parse_doc(doc)
        if discriminating_union:
            assert parsed_table == table
        else:
            assert parsed_table.material == table.material
            # parsed_table.shape is an "upcasted" Shape instance of the original shape
            assert parsed_table.shape == Shape(**table.shape.dict())
