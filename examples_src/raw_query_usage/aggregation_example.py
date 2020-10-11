from odmantic import AIOEngine, Model


class Rectangle(Model):
    length: float
    width: float


rectangles = [
    Rectangle(length=0.1, width=1),
    Rectangle(length=3.5, width=1),
    Rectangle(length=2.87, width=5.19),
    Rectangle(length=1, width=10),
    Rectangle(length=0.1, width=100),
]

engine = AIOEngine()
await engine.save_all(rectangles)

collection = engine.get_collection(Rectangle)
pipeline = []
# Add an area field
pipeline.append(
    {
        "$addFields": {
            "area": {
                "$multiply": [++Rectangle.length, ++Rectangle.width]
            }  # Compute the area remotely
        }
    }
)
# Filter only rectanges with an area lower than 10
pipeline.append({"$match": {"area": {"$lt": 10}}})
# Project to keep only the defined fields (this step is optional)
pipeline.append(
    {
        "$project": {
            +Rectangle.length: True,
            +Rectangle.width: True,
        }  # Specifying "area": False is unnecessary here
    }
)
documents = await collection.aggregate(pipeline).to_list(length=None)
small_rectangles = [Rectangle.parse_doc(doc) for doc in documents]
print(small_rectangles)
#> [
#>     Rectangle(id=ObjectId("..."), length=0.1, width=1.0),
#>     Rectangle(id=ObjectId("..."), length=3.5, width=1.0),
#> ]
