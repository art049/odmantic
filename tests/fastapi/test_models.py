from inspect import getdoc
from typing import Type

import pytest
from bson import ObjectId as BSONObjectId

from odmantic import Model, ObjectId
from odmantic.bson import BaseBSONModel, Binary, Decimal128, Int64, Regex
from odmantic.model import EmbeddedModel


def test_object_id_fastapi_get_query(fastapi_app, test_client):
    value_injected = None

    @fastapi_app.get("/{id}")
    def get(id: ObjectId):
        nonlocal value_injected
        value_injected = id
        return "ok"

    id_get_str = "5f79d7e8b305f24ca43593e2"
    test_client.get(f"/{id_get_str}")
    assert value_injected == BSONObjectId(id_get_str)


def test_object_id_fastapi_get_query_invalid_id(fastapi_app, test_client):
    @fastapi_app.get("/{id}")
    def get(id: ObjectId):
        return "ok"

    invalid_oid_str = "a"
    response = test_client.get(f"/{invalid_oid_str}")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "id"]


@pytest.mark.skip("Need to specify custom json_encoder or to use a root_type")
def test_object_id_fastapi_response(fastapi_app, test_client):
    id_get_str = "5f79d7e8b305f24ca43593e2"

    @fastapi_app.get("/")
    def get():
        return {"id": ObjectId(id_get_str)}

    response = test_client.get("/")
    assert response.json() == {"id": id_get_str}


def test_object_id_fastapi_pydantic_response_model(fastapi_app, test_client):
    id_get_str = "5f79d7e8b305f24ca43593e2"

    class PydanticModel(BaseBSONModel):
        id: ObjectId

        class Config:
            """Defining a config object WITHOUT json_encoders arguments"""

    @fastapi_app.get("/", response_model=PydanticModel)
    def get():
        return {"id": ObjectId(id_get_str)}

    response = test_client.get("/")
    assert response.json() == {"id": id_get_str}


def test_object_id_fastapi_odmantic_response_pydantic_model(fastapi_app, test_client):
    class ODMModel(Model):
        ...

    object = ODMModel()

    @fastapi_app.get("/", response_model=ODMModel.__pydantic_model__)
    def get():
        return object

    response = test_client.get("/")
    assert response.json() == {"id": str(object.id)}


def test_object_id_fastapi_odmantic_response_model(fastapi_app, test_client):
    class ODMModel(Model):
        ...

    object = ODMModel()

    @fastapi_app.get("/", response_model=ODMModel)
    def get():
        return object

    response = test_client.get("/")
    assert response.json() == {"id": str(object.id)}


def test_openapi_json_with_bson_fields(fastapi_app, test_client):
    class ODMModel(Model):
        oid: ObjectId
        int64: Int64
        decimal: Decimal128
        binary: Binary
        regex: Regex

    @fastapi_app.get("/", response_model=ODMModel)
    def get():
        return None

    response = test_client.get("/openapi.json")
    assert response.status_code == 200


@pytest.mark.parametrize("base", (Model, EmbeddedModel))
def test_docstring_not_nullified(base: Type):
    class M(base):  # type: ignore
        """My docstring"""

    doc = getdoc(M)
    assert doc is None or doc == "My docstring"
    description = M.schema()["description"]
    assert description == "My docstring"


@pytest.mark.parametrize("base", (Model, EmbeddedModel))
def test_docstring_nullified(base: Type):
    class M(base):  # type: ignore
        ...

    doc = getdoc(M)
    assert doc == ""
    assert "description" not in M.schema()


@pytest.mark.parametrize("base", (Model, EmbeddedModel, BaseBSONModel))
def test_base_classes_docstring_not_nullified(base: Type):
    doc = getdoc(base)
    assert doc is not None and doc != ""
