from typing import Dict
from unittest.mock import patch

import pytest
from async_asgi_testclient import TestClient

from docs.examples_src.usage_fastapi.base_example import Tree
from odmantic.engine import AIOEngine

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def base_example_client(engine: AIOEngine) -> TestClient:
    with patch("docs.examples_src.usage_fastapi.base_example.engine", engine):
        from docs.examples_src.usage_fastapi.base_example import app

        async with TestClient(app) as client:
            yield client


EXAMPLE_TREE_BODY = dict(name="MyTree", average_size=152, discovery_year=1992)


async def test_create_tree(base_example_client: TestClient, engine: AIOEngine):
    response = await base_example_client.put("/trees/", json=EXAMPLE_TREE_BODY)
    assert response.status_code == 200
    assert await engine.find_one(Tree, EXAMPLE_TREE_BODY) is not None


def is_sub_dict(a: Dict, b: Dict) -> bool:
    return set(a.items()).issubset(set(b.items()))


@pytest.mark.parametrize("count", [2, 10])
async def test_create_trees_count_get(
    base_example_client: TestClient, engine: AIOEngine, count: int
):

    for _ in range(count):
        response = await base_example_client.put("/trees/", json=EXAMPLE_TREE_BODY)
        assert response.status_code == 200
    assert await engine.count(Tree) == count
    async for tree in engine.find(Tree):
        assert is_sub_dict(EXAMPLE_TREE_BODY, tree.dict())


async def test_get_tree_by_id(base_example_client: TestClient, engine: AIOEngine):
    tree = Tree(**EXAMPLE_TREE_BODY)
    await engine.save(tree)
    response = await base_example_client.get(
        f"/trees/{tree.id}", json=EXAMPLE_TREE_BODY
    )
    assert response.status_code == 200
    assert Tree(**response.json()) == tree


@pytest.fixture
async def example_update_client(engine: AIOEngine) -> TestClient:
    with patch("docs.examples_src.usage_fastapi.example_update.engine", engine):
        from docs.examples_src.usage_fastapi.example_update import app

        async with TestClient(app) as client:
            yield client


PATCHED_NAME = "New Tree Name"


async def test_update_tree_name_by_id(
    example_update_client: TestClient, engine: AIOEngine
):
    tree = Tree(**EXAMPLE_TREE_BODY)
    await engine.save(tree)
    response = await example_update_client.patch(
        f"/trees/{tree.id}", json=dict(name=PATCHED_NAME)
    )
    assert response.status_code == 200
    assert response.json()["name"] == PATCHED_NAME
    assert await engine.find_one(Tree, {"name": PATCHED_NAME}) is not None


@pytest.fixture
async def example_delete_client(engine: AIOEngine) -> TestClient:
    with patch("docs.examples_src.usage_fastapi.example_delete.engine", engine):
        from docs.examples_src.usage_fastapi.example_delete import app

        async with TestClient(app) as client:
            yield client


async def test_delete_tree_by_id(example_delete_client: TestClient, engine: AIOEngine):
    tree = Tree(**EXAMPLE_TREE_BODY)
    await engine.save(tree)
    # Create other trees not affected by the delete to come
    for _ in range(10):
        await engine.save(Tree(**EXAMPLE_TREE_BODY))
    response = await example_delete_client.delete(f"/trees/{tree.id}")
    assert response.status_code == 200
    assert await engine.find_one(Tree, Tree.id == tree.id) is None
