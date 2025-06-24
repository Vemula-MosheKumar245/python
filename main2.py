from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ✅ PostgreSQL connection URL — update it with your actual credentials
DATABASE_URL = "postgresql+psycopg2://postgres:root@localhost/Linda"

# ✅ SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# ✅ Create FastAPI app
app = FastAPI()

# ✅ Define database table structure
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    mobile = Column(String)

# ✅ Create the table if it doesn’t already exist
Base.metadata.create_all(bind=engine)

# ✅ Define request model using Pydantic
class UserIn(BaseModel):
    name: str
    mobile: str

# ✅ POST endpoint: add user to the database
@app.post("/add")
def add_user(user: UserIn):
    db = SessionLocal()
    db_user = User(name=user.name, mobile=user.mobile)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.name == user.name).first()
    if existing_user:
        db.close()
        raise HTTPException(status_code=400, detail="User with this name already exists")

    try:
        db.add(db_user)
        db.commit()
        return {"message": "User added successfully", "name": user.name, "mobile": user.mobile}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error adding user")
    finally:
        db.close()

# ✅ GET endpoint: retrieve user by name
@app.get("/get")
def get_user(name: str):
    db = SessionLocal()
    user = db.query(User).filter(User.name == name).first()
    db.close()

    if user:
        return {"name": user.name, "mobile": user.mobile}
    else:
        raise HTTPException(status_code=404, detail="User not found")
