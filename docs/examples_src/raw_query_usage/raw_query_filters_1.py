engine.find(Tree, Tree.average_size > 2)
engine.find(Tree, {+Tree.average_size: {"$gt": 2}})
engine.find(Tree, {"average_size": {"$gt": 2}})
