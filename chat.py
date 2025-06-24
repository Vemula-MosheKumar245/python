# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from sqlalchemy import create_engine, Column, Integer, String, Text
# from sqlalchemy.orm import sessionmaker, declarative_base
# import google.generativeai as genai
# import uuid

# # ==== Gemini AI Setup ====
# genai.configure(api_key="AIzaSyDwoHNR0OPHd-AfyH_pFeaYllPdi41O9wY")
# model = genai.GenerativeModel("models/gemini-1.5-flash")

# # ==== PostgreSQL Setup ====
# DATABASE_URL = "postgresql+psycopg2://postgres:root@localhost/Linda"

# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# class Chat(Base):
#     __tablename__ = "chats"
#     id = Column(Integer, primary_key=True, index=True)
#     session_id = Column(String, unique=True, index=True)
#     user_message = Column(Text)
#     bot_response = Column(Text)

# Base.metadata.create_all(bind=engine)

# # ==== FastAPI Init ====
# app = FastAPI()

# # ==== Pydantic Schema ====
# class Message(BaseModel):
#     message: str

# # ==== POST /chat ====
# @app.post("/chat/")
# def send_message(msg: Message):
#     session_id = str(uuid.uuid4())

#     try:
#         # Get Gemini response
#         response = model.generate_content(msg.message)
#         answer = response.text.strip()

#         # Save to DB
#         db = SessionLocal()
#         chat = Chat(session_id=session_id, user_message=msg.message, bot_response=answer)
#         db.add(chat)
#         db.commit()
#         db.close()

#         return {"session_id": session_id}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")

# # ==== GET /chat/{session_id} ====
# @app.get("/chat/{session_id}")
# def get_response(session_id: str):
#     db = SessionLocal()
#     chat = db.query(Chat).filter(Chat.session_id == session_id).first()
#     db.close()

#     if not chat:
#         raise HTTPException(status_code=404, detail="Session not found")

#     return {"question": chat.user_message, "answer": chat.bot_response}
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware


# ==== Gemini AI Setup ====
genai.configure(api_key="AIzaSyDwoHNR0OPHd-AfyH_pFeaYllPdi41O9wY")
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

# ==== FastAPI Init ====
app = FastAPI()

# ==== Pydantic Schema ====
class Message(BaseModel):
    message: str

# ==== POST /chat ====
@app.post("/chat/")
def send_message(msg: Message):
    try:
        # Append instruction to user message
        modified_message = f"{msg.message.strip()} Please give the answer within one sentence."

        # Send modified message to Gemini
        response = model.generate_content(modified_message)
        answer = response.text.strip()

        # Return response to frontendS
        return {
            "question": msg.message,
            "answer": answer
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"] if you prefer strict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
