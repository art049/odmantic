book = await engine.find_one(Book, Book.title == "Python Cookbook")
authors = await engine.find(Author, Author.id.in_(book.author_ids))
print(authors)
#> [
#>   Author(id=ObjectId("5f7a37dc7311be1362e1da4e"), name="David Beazley"),
#>   Author(id=ObjectId("5f7a37dc7311be1362e1da4f"), name="Brian K. Jones"),
#> ]
