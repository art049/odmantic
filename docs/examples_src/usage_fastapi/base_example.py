from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException

from odmantic import AIOEngine, Model, ObjectId
from odmantic.fastapi import AIOEngineDependency


class Tree(Model):
    name: str
    average_size: float
    discovery_year: int


app = FastAPI()

EngineD = AIOEngineDependency()


@app.put("/trees/", response_model=Tree)
async def create_tree(tree: Tree, engine: AIOEngine = EngineD):
    await engine.save(tree)
    return tree


@app.get("/trees/", response_model=List[Tree])
async def get_trees(engine: AIOEngine = EngineD):
    trees = await engine.find(Tree)
    return trees


@app.get("/trees/count", response_model=int)
async def count_trees(engine: AIOEngine = EngineD):
    count = await engine.count(Tree)
    return count


@app.get("/trees/{id}", response_model=Tree)
async def get_tree_by_id(id: ObjectId, engine: AIOEngine = EngineD):
    tree = await engine.find_one(Tree, Tree.id == id)
    if tree is None:
        raise HTTPException(404)
    return tree


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8080)
