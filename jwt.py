from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, validator
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi import Query
import pyotp
import qrcode
import io
import base64

# -------------------- Database Setup --------------------
DATABASE_URL = "postgresql+psycopg2://postgres:root@localhost/Linda"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# -------------------- JWT Config --------------------
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# -------------------- Password Hashing --------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------- Models --------------------
class User(Base):
    __tablename__ = "jack"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    secret_key = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# -------------------- Pydantic Schemas --------------------
class RegisterRequest(BaseModel):
    email: str
    password: str

    @validator('email')
    def validate_email_format(cls, value):
        if '@' not in value or not value.endswith('.com'):
            raise ValueError("Email must contain '@' and end with '.com'")
        return value

class VerifyRequest(BaseModel):
    email: str
    otp: str

class QRRequest(BaseModel):
    email: str

class LoginRequest(BaseModel):
    email: str
    password: str

    @validator('email')
    def validate_email_format(cls, value):
        if '@' not in value or not value.endswith('.com'):
            raise ValueError("Email must contain '@' and end with '.com'")
        return value

# -------------------- FastAPI App --------------------
app = FastAPI()

# -------------------- Dependency --------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- JWT Utility --------------------
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# -------------------- Register Endpoint --------------------
@app.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=request.email).first()

    if user:
        raise HTTPException(status_code=400, detail="User already exists. Please login or verify OTP.")

    hashed = pwd_context.hash(request.password)
    secret = pyotp.random_base32()

    new_user = User(
        email=request.email,
        hashed_password=hashed,
        secret_key=secret,
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully. Please scan the QR code using the /scanqr endpoint."}

# -------------------- QR Code Base64 Endpoint -------------------

@app.post("/scanqr")
def generate_qr(request: QRRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=request.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="User already authenticated with 2FA")

    totp = pyotp.TOTP(user.secret_key)
    uri = totp.provisioning_uri(name=request.email, issuer_name="MyApp") 

    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_bytes = buf.getvalue()
    base64_str = base64.b64encode(img_bytes).decode("utf-8")

    full_base64_str = f"data:image/png;base64,{base64_str}"

    return {"qr_code_base64": full_base64_str}


# -------------------- OTP Verification After Register --------------------
@app.post("/verify")
def verify_otp(request: VerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    totp = pyotp.TOTP(user.secret_key)
    if not totp.verify(request.otp):
        raise HTTPException(status_code=401, detail="Invalid OTP")

    user.is_verified = True
    db.commit()

    token = create_access_token(data={"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "message": "OTP verified successfully. You are now logged in."
    }

# -------------------- Login Endpoint --------------------
@app.post("/login")
def login_status_check(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=request.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not pwd_context.verify(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    return {
        "email": user.email,
        "is_verified": user.is_verified
    }

# -------------------- Additional OTP Verification After Login --------------------
@app.post("/verify-after-login")
def verify_otp_post_login(request: VerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    totp = pyotp.TOTP(user.secret_key)
    if not totp.verify(request.otp):
        raise HTTPException(status_code=401, detail="Invalid OTP after login")

    return {"message": "OTP verified after login. You can now access sensitive operations."}

# -------------------- Disable 2FA Endpoint --------------------
@app.post("/disable-2fa")
def disable_2fa(email: str = Body(...), password: str = Body(...), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=email).first()

    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_verified:
        raise HTTPException(status_code=400, detail="2FA is already disabled for this user")

    user.is_verified = False
    user.secret_key = pyotp.random_base32()
    db.commit()

    return {
        "message": "2FA disabled successfully. Please scan the new QR code and verify OTP again."
    }

# -------------------- CORS Middleware --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
