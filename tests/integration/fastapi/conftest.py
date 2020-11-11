import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def fastapi_app():
    return FastAPI()


@pytest.fixture
def test_client(fastapi_app):
    return TestClient(fastapi_app)
