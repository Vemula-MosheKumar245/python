from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
import strawberry
from typing import List, AsyncGenerator
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import asyncio

# ========== DATABASE SETUP ==========
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========== SQLAlchemy MODEL ==========
class AuthorModel(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

Base.metadata.create_all(bind=engine)

# ========== DEPENDENCY ==========
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========== SUBSCRIPTION STORAGE ==========
subscribers: List[asyncio.Queue] = []

async def notify_subscribers(author_data):
    for queue in subscribers:
        await queue.put(author_data)

# ========== STRAWBERRY TYPES ==========
@strawberry.type
class Author:
    id: int
    name: str
    email: str

# ========== QUERY ==========
@strawberry.type
class Query:
    @strawberry.field
    def authors(self) -> List[Author]:
        db = next(get_db())
        authors = db.query(AuthorModel).all()
        return [Author(id=a.id, name=a.name, email=a.email) for a in authors]

# ========== MUTATION ==========
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_author(self, name: str, email: str) -> Author:
        db = next(get_db())
        existing = db.query(AuthorModel).filter_by(email=email).first()
        if existing:
            raise Exception("Email already exists.")
        author = AuthorModel(name=name, email=email)
        db.add(author)
        db.commit()
        db.refresh(author)
        result = Author(id=author.id, name=author.name, email=author.email)
        await notify_subscribers(result)
        return result

    @strawberry.mutation
    def delete_author(self, email: str) -> bool:
        db = next(get_db())
        author = db.query(AuthorModel).filter_by(email=email).first()
        if not author:
            raise Exception("Author not found.")
        db.delete(author)
        db.commit()
        return True

# ========== SUBSCRIPTION ==========
@strawberry.type
class Subscription:
    @strawberry.subscription
    async def author_added(self) -> AsyncGenerator[Author, None]:
        queue: asyncio.Queue = asyncio.Queue()
        subscribers.append(queue)
        try:
            while True:
                author = await queue.get()
                yield author
        finally:
            subscribers.remove(queue)

# ========== SCHEMA & APP ==========
schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
def read_root():
    return {"message": "Visit /graphql for Playground. Subscriptions require WebSocket (ws://)"}
