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


@app.get("/trees/{id}", response_model=Tree)
async def get_tree_by_id(id: ObjectId, engine: AIOEngine = EngineD):
    tree = await engine.find_one(Tree, Tree.id == id)
    if tree is None:
        raise HTTPException(404)
    return tree


@app.delete("/trees/{id}", response_model=Tree)
async def delete_tree_by_id(id: ObjectId, engine: AIOEngine = EngineD):
    tree = await engine.find_one(Tree, Tree.id == id)
    if tree is None:
        raise HTTPException(404)
    await engine.delete(tree)
    return tree


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8080)
