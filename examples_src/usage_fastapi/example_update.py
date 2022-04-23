from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from odmantic import AIOEngine, Model, ObjectId


class Tree(Model):
    name: str
    average_size: float
    discovery_year: int


app = FastAPI()

engine = AIOEngine()


@app.get("/trees/{id}", response_model=Tree)
async def get_tree_by_id(id: ObjectId):
    tree = await engine.find_one(Tree, Tree.id == id)
    if tree is None:
        raise HTTPException(404)
    return tree


class TreePatchSchema(BaseModel):
    name: str = None
    average_size: float = None
    discovery_year: float = None


@app.patch("/trees/{id}", response_model=Tree)
async def update_tree_by_id(id: ObjectId, patch: TreePatchSchema):
    tree = await engine.find_one(Tree, Tree.id == id)
    if tree is None:
        raise HTTPException(404)
    tree.update(patch)
    await engine.save(tree)
    return tree
