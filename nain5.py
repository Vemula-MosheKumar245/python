from fastapi import FastAPI
import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional
from datetime import datetime


products_db = [
    {"id": 1, "name": "Laptop", "price": 1200.00},
    {"id": 2, "name": "Phone", "price": 800.00},
    {"id": 3, "name": "Headphones", "price": 150.00},
]

orders_db = []  


@strawberry.type
class Product:
    id: int
    name: str
    price: float


@strawberry.type
class Order:
    id: int
    product: Product
    quantity: int
    total_price: float
    order_date: datetime


@strawberry.type
class Query:

    @strawberry.field
    def products(self) -> List[Product]:
        return [Product(**p) for p in products_db]

    @strawberry.field
    def orders(self) -> List[Order]:
        return orders_db


@strawberry.type
class Mutation:

    @strawberry.mutation
    def create_order(self, product_id: int, quantity: int) -> Order:
        
        product_data = next((p for p in products_db if p["id"] == product_id), None)
        if not product_data:
            raise ValueError("Product not found")

        total = product_data["price"] * quantity
        order = Order(
            id=len(orders_db) + 1,
            product=Product(**product_data),
            quantity=quantity,
            total_price=total,
            order_date=datetime.now()
        )
        orders_db.append(order)
        return order


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
