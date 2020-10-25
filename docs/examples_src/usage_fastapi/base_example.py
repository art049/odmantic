from typing import List

from fastapi import FastAPI, HTTPException

from odmantic import AIOEngine, Model, ObjectId


class Tree(Model):
    name: str
    average_size: float
    discovery_year: int


app = FastAPI()

engine = AIOEngine()


@app.put("/trees/", response_model=Tree)
async def create_tree(tree: Tree):
    await engine.save(tree)
    return tree


@app.get("/trees/", response_model=List[Tree])
async def get_trees():
    trees = await engine.find(Tree)
    return trees


@app.get("/trees/count", response_model=int)
async def count_trees():
    count = await engine.count(Tree)
    return count


@app.get("/trees/{id}", response_model=Tree)
async def get_tree_by_id(id: ObjectId):
    tree = await engine.find_one(Tree, Tree.id == id)
    if tree is None:
        raise HTTPException(404)
    return tree
