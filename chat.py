import asyncio
from datetime import datetime
from typing import List, AsyncGenerator

import strawberry
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter


# In-memory message storage
messages_db: List["Message"] = []
subscribers: List[asyncio.Queue] = []


@strawberry.type
class Message:
    content: str
    from_user: str
    to_user: str
    timestamp: datetime


@strawberry.type
class Query:
    @strawberry.field
    def messages(self) -> List[Message]:
        return messages_db


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def send_message(self, content: str, from_user: str, to_user: str) -> Message:
        message = Message(
            content=content,
            from_user=from_user,
            to_user=to_user,
            timestamp=datetime.now()
        )
        messages_db.append(message)

        # Notify all subscribers
        for queue in subscribers:
            await queue.put(message)

        return message


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def message_stream(
        self, from_user: str, to_user: str
    ) -> AsyncGenerator[Message, None]:
        queue: asyncio.Queue = asyncio.Queue()
        subscribers.append(queue)

        try:
            while True:
                message: Message = await queue.get()
                if (
                    (message.from_user == from_user and message.to_user == to_user)
                    or
                    (message.from_user == to_user and message.to_user == from_user)
                ):
                    yield message
        finally:
            subscribers.remove(queue)


# Create schema with query, mutation, and subscription
schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
graphql_app = GraphQLRouter(schema)

# Create FastAPI app
app = FastAPI()

# Add CORS middleware (important for WebSocket & frontend use)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, use your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")
