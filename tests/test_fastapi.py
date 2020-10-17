import pytest
from bson import ObjectId as BSONObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

from odmantic import Model, ObjectId
from odmantic.bson import BaseBSONModel


@pytest.fixture
def fastapi_app():
    return FastAPI()


@pytest.fixture
def test_client(fastapi_app):
    return TestClient(fastapi_app)


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


@pytest.mark.skip("Need to specify custom json_encoder")
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


def test_object_id_fastapi_odmantic_response_base_model(fastapi_app, test_client):
    class ODMModel(Model):
        ...

    object = ODMModel()

    @fastapi_app.get("/", response_model=ODMModel.__base_model__)
    def get():
        return object

    response = test_client.get("/")
    assert response.json() == {"id": str(object.id)}


@pytest.mark.skip("Depends on the basemodel shadowing attributes: pydantic issue #242")
def test_object_id_fastapi_odmantic_response_model(fastapi_app, test_client):
    class ODMModel(Model):
        ...

    object = ODMModel()

    @fastapi_app.get("/", response_model=ODMModel)
    def get():
        return object

    response = test_client.get("/")
    assert response.json() == {"id": str(object.id)}
