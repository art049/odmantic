from odmantic import Field, Index, Model


class Product(Model):
    name: str = Field(index=True)
    stock: int
    category: str
    sku: str = Field(unique=True)

    class Config:
        @staticmethod
        def indexes():
            yield Index(Product.name, Product.stock, name="name_stock_index")
            yield Index(Product.name, Product.category, unique=True)
