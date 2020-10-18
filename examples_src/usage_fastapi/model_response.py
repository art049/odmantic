from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException

from odmantic import AIOEngine, Model, ObjectId
from odmantic.fastapi import AIOEngineDependency


class TreeModel(Model):
    """My Tree Model"""

    name: str
    average_size: float
    discovery_year: int


app = FastAPI()

EngineD = AIOEngineDependency()


@app.post("/trees/", response_model=TreeModel)
async def create_tree(tree: TreeModel, engine: AIOEngine = EngineD):
    await engine.save(tree)
    return tree


@app.get("/trees/", response_model=List[TreeModel])
async def get_trees(engine: AIOEngine = EngineD):
    trees = await engine.find(TreeModel)
    return trees


@app.get("/trees/{id}", response_model=TreeModel)
async def get_tree_by_id(id: ObjectId, engine: AIOEngine = EngineD):
    tree = await engine.find_one(TreeModel, TreeModel.id == id)
    if tree is None:
        raise HTTPException(404)
    return tree


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8080)
