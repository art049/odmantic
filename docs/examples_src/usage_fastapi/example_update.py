from typing import Optional

import uvicorn
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
    name: Optional[str]
    average_size: Optional[float]
    discovery_year: Optional[float]


@app.patch("/trees/{id}", response_model=Tree)
async def update_tree_by_id(id: ObjectId, patch: TreePatchSchema):
    tree = await engine.find_one(Tree, Tree.id == id)
    if tree is None:
        raise HTTPException(404)

    patch_dict = patch.dict(exclude_unset=True)
    for name, value in patch_dict.items():
        setattr(tree, name, value)
    await engine.save(tree)
    return tree
