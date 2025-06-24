# from fastapi import FastAPI
# from strawberry.fastapi import GraphQLRouter
# from app.graphql_schema import schema
 
# app = FastAPI()
 
# graphql_app = GraphQLRouter(schema)
# app.include_router(graphql_app, prefix="/graphql")
 
# @app.get("/")
# def test():
#     return {"msg": "FastAPI is working"}
 
 
# from fastapi import FastAPI, Request, Form
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from strawberry.fastapi import GraphQLRouter
# from app.graphql_schema import schema
# from app.pubsub import pubsub
# from app.types import Message
# from datetime import datetime
 
# app = FastAPI()
# graphql_app = GraphQLRouter(schema)
# app.include_router(graphql_app, prefix="/graphql")
 
# templates = Jinja2Templates(directory="app/templates")
 
# @app.get("/", response_class=HTMLResponse)
# def form_page(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})
 
# @app.post("/", response_class=HTMLResponse)
# async def send_message(
#     request: Request,
#     content: str = Form(...),
#     fromUser: str = Form(...),
#     toUser: str = Form(...)
# ):
#     msg = Message(
#         content=content,
#         fromUser=fromUser,
#         toUser=toUser,
#         timestamp=datetime.utcnow().isoformat()
#     )
#     await pubsub.publish(msg)
#     return templates.TemplateResponse("index.html", {
#         "request": request,
#         "message": msg,
#         "success": True
#     })
 
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from strawberry.fastapi import GraphQLRouter
from datetime import datetime
 
from app.graphql_schema import schema, stored_messages
from app.types import Message
 
app = FastAPI()
templates = Jinja2Templates(directory="templates")
 
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
 
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "messages": stored_messages[::-1],
        "success": False
    })
 
@app.post("/", response_class=HTMLResponse)
async def post_message(
    request: Request,
    content: str = Form(...),
    fromUser: str = Form(...),
    toUser: str = Form(...)
):
    timestamp = datetime.utcnow().isoformat()
    msg = Message(content=content, fromUser=fromUser, toUser=toUser, timestamp=timestamp)
    stored_messages.append(msg)
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "success": True,
        "message": msg,
        "messages": stored_messages[::-1]
    })
 
 