# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
# from sqlalchemy.orm import relationship, sessionmaker, declarative_base
# from typing import List
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

# # ---------- Database Setup ----------
# DATABASE_URL = "postgresql+psycopg2://postgres:root@localhost/Linda"

# Base = declarative_base()
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# # ---------- FastAPI Setup ----------
# app = FastAPI()

# # ---------- CORS Setup ----------
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],  # React frontend
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ---------- SQLAlchemy Models ----------
# class Category(Base):
#     __tablename__ = "category"
#     id = Column(Integer, primary_key=True, index=True)
#     category = Column(String, unique=True, index=True)
#     questions = relationship("Question", back_populates="category")

# class Question(Base):
#     __tablename__ = "questions"
#     id = Column(Integer, primary_key=True, index=True)
#     category_id = Column(Integer, ForeignKey("category.id"))
#     question = Column(String, nullable=False)
#     answer = Column(String, nullable=False)
#     category = relationship("Category", back_populates="questions")

# Base.metadata.create_all(bind=engine)

# # ---------- Pydantic Schemas ----------
# class CategoryIn(BaseModel):
#     category: str

# class CategoryOut(BaseModel):
#     id: int
#     category: str
#     model_config = {"from_attributes": True}

# class QuestionIn(BaseModel):
#     category_id: int
#     question: str
#     answer: str

# class QuestionOut(BaseModel):
#     id: int
#     category_id: int
#     question: str
#     answer: str
#     model_config = {"from_attributes": True}

# class AnswerSubmission(BaseModel):
#     question_id: int
#     submitted_answer: str

# class SubmissionNoCategory(BaseModel):
#     email: str
#     name: str
#     answers: List[AnswerSubmission]

# class SubmissionResultNoCategory(BaseModel):
#     email: str
#     name: str
#     total_questions: int
#     correct_answers: int
#     score: float

# # ---------- Routes ----------

# # Add category
# @app.post("/categories/", response_model=CategoryOut)
# def add_category(cat: CategoryIn):
#     db = SessionLocal()
#     existing_category = db.query(Category).filter(Category.category == cat.category).first()
#     if existing_category:
#         db.close()
#         raise HTTPException(status_code=400, detail="Category already exists")
#     new_category = Category(category=cat.category)
#     db.add(new_category)
#     db.commit()
#     db.refresh(new_category)
#     db.close()
#     return new_category

# # Get all categories
# @app.get("/categories/", response_model=List[CategoryOut])
# def get_all_categories():
#     db = SessionLocal()
#     try:
#         return db.query(Category).all()
#     finally:
#         db.close()

# # Add question
# @app.post("/questions/")
# def add_question(q: QuestionIn):
#     db = SessionLocal()
#     category = db.query(Category).filter(Category.id == q.category_id).first()
#     if not category:
#         db.close()
#         raise HTTPException(status_code=404, detail="Category not found")
#     new_question = Question(category_id=q.category_id, question=q.question, answer=q.answer)
#     db.add(new_question)
#     db.commit()
#     db.close()
#     return {"message": "Question added successfully"}

# # Get questions by category
# @app.get("/questions/{category_id}", response_model=List[QuestionOut])
# def get_questions_by_category(category_id: int):
#     db = SessionLocal()
#     try:
#         questions = db.query(Question).filter(Question.category_id == category_id).all()
#         return questions
#     finally:
#         db.close()

# # Submit answers
# @app.post("/submit/", response_model=SubmissionResultNoCategory)
# def submit_answers_no_category(submission: SubmissionNoCategory):
#     db = SessionLocal()
#     try:
#         question_ids = [ans.question_id for ans in submission.answers]

#         if not question_ids:
#             raise HTTPException(status_code=400, detail="No answers submitted")

#         if len(set(question_ids)) != len(question_ids):
#             raise HTTPException(status_code=400, detail="Duplicate question IDs submitted")

#         for ans in submission.answers:
#             if not ans.submitted_answer.strip():
#                 raise HTTPException(status_code=400, detail=f"Answer for question ID {ans.question_id} is empty")

#         questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
#         db_question_ids = {q.id for q in questions}
#         missing_ids = set(question_ids) - db_question_ids
#         if missing_ids:
#             raise HTTPException(status_code=400, detail=f"Question IDs not found: {list(missing_ids)}")

#         correct_answers_map = {q.id: q.answer.strip().lower() for q in questions}
#         correct_count = 0

#         for ans in submission.answers:
#             if correct_answers_map.get(ans.question_id) == ans.submitted_answer.strip().lower():
#                 correct_count += 1

#         total_questions = len(question_ids)
#         score_percentage = (correct_count / total_questions) * 100

#         try:
#             send_result_email_gmail(
#                 to_email=submission.email,
#                 name=submission.name,
#                 total_questions=total_questions,
#                 correct_answers=correct_count,
#                 score=round(score_percentage, 2)
#             )
#         except Exception as e:
#             print(f"Failed to send email: {e}")

#         return SubmissionResultNoCategory(
#             email=submission.email,
#             name=submission.name,
#             total_questions=total_questions,
#             correct_answers=correct_count,
#             score=round(score_percentage, 2)
#         )
#     finally:
#         db.close()

# # ---------- Email Sending ----------
# def send_result_email_gmail(to_email: str, name: str, total_questions: int, correct_answers: int, score: float):
#     sender_email = "prameelarani769@gmail.com"
#     sender_password = "cnzb wdwn vkix vprz"  # Gmail App Password

#     smtp_server = "smtp.gmail.com"
#     smtp_port = 587

#     subject = "Your Quiz Results"
#     body = f"""
#     Hello {name},

#     Thank you for completing the quiz!

#     Total Questions: {total_questions}
#     Correct Answers: {correct_answers}
#     Score: {score}%

#     Regards,
#     Quiz Team
#     """

#     message = MIMEMultipart()
#     message["From"] = sender_email
#     message["To"] = to_email
#     message["Subject"] = subject
#     message.attach(MIMEText(body, "plain"))

#     with smtplib.SMTP(smtp_server, smtp_port) as server:
#         server.starttls()
#         server.login(sender_email, sender_password)
#         server.sendmail(sender_email, to_email, message.as_string())
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from typing import List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------- Database Setup ----------
DATABASE_URL = "postgresql+psycopg2://postgres:root@localhost/Linda"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# ---------- FastAPI Setup ----------
app = FastAPI()

# ---------- CORS Setup ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- SQLAlchemy Models ----------
class Category(Base):
    __tablename__ = "category"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, unique=True, index=True)
    questions = relationship("Question", back_populates="category")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("category.id"))
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'text', 'integer', 'both'
    max_limit = Column(Integer, nullable=True)  # Optional character/digit limit

    category = relationship("Category", back_populates="questions")

Base.metadata.create_all(bind=engine)

# ---------- Pydantic Schemas ----------
class CategoryIn(BaseModel):
    category: str

class CategoryOut(BaseModel):
    id: int
    category: str
    model_config = {"from_attributes": True}

class QuestionIn(BaseModel):
    category_id: int
    question: str
    answer: str
    type: str
    max_limit: int | None = None

class QuestionOut(BaseModel):
    id: int
    category_id: int
    question: str
    answer: str
    type: str
    max_limit: int | None = None
    model_config = {"from_attributes": True}

class AnswerSubmission(BaseModel):
    question_id: int
    submitted_answer: str

class SubmissionNoCategory(BaseModel):
    email: str
    name: str
    answers: List[AnswerSubmission]

class SubmissionResultNoCategory(BaseModel):
    email: str
    name: str
    total_questions: int
    correct_answers: int
    score: int

# ---------- Routes ----------
@app.post("/categories/", response_model=CategoryOut)
def add_category(cat: CategoryIn):
    db = SessionLocal()
    existing_category = db.query(Category).filter(Category.category == cat.category).first()
    if existing_category:
        db.close()
        raise HTTPException(status_code=400, detail="Category already exists")
    new_category = Category(category=cat.category)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    db.close()
    return new_category

@app.get("/categories/", response_model=List[CategoryOut])
def get_all_categories():
    db = SessionLocal()
    try:
        return db.query(Category).all()
    finally:
        db.close()

@app.post("/questions/")
def add_question(q: QuestionIn):
    db = SessionLocal()
    category = db.query(Category).filter(Category.id == q.category_id).first()
    if not category:
        db.close()
        raise HTTPException(status_code=404, detail="Category not found")

    if q.type not in ("text", "integer", "boolean","both"):
        db.close()
        raise HTTPException(status_code=400, detail="Invalid type. Use 'text', 'integer', 'boolean','both'.")

    new_question = Question(
        category_id=q.category_id,
        question=q.question,
        answer=q.answer,
        type=q.type,
        max_limit=q.max_limit
    )
    db.add(new_question)
    db.commit()
    db.close()
    return {"message": "Question added successfully"}

@app.get("/questions/{category_id}", response_model=List[QuestionOut])
def get_questions_by_category(category_id: int):
    db = SessionLocal()
    try:
        questions = db.query(Question).filter(Question.category_id == category_id).all()
        return questions
    finally:
        db.close()

@app.post("/submit/", response_model=SubmissionResultNoCategory)
def submit_answers_no_category(submission: SubmissionNoCategory):
    db = SessionLocal()
    try:
        question_ids = [ans.question_id for ans in submission.answers]

        if not question_ids:
            raise HTTPException(status_code=400, detail="No answers submitted")

        if len(set(question_ids)) != len(question_ids):
            raise HTTPException(status_code=400, detail="Duplicate question IDs submitted")

        questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
        db_question_ids = {q.id for q in questions}
        missing_ids = set(question_ids) - db_question_ids
        if missing_ids:
            raise HTTPException(status_code=400, detail=f"Question IDs not found: {list(missing_ids)}")

        correct_answers_map = {q.id: q.answer.strip().lower() for q in questions}
        correct_count = 0
        wrong_count = 0
        skipped_count = 0
        total_marks = 0

        for ans in submission.answers:
            user_ans = ans.submitted_answer.strip().lower()
            correct_ans = correct_answers_map.get(ans.question_id)

            if not user_ans:
                skipped_count += 1
                continue 

            if user_ans == correct_ans:
                correct_count += 1
                total_marks += 3 
            else:
                wrong_count += 1
                total_marks -= 1 

        total_questions = len(question_ids)

        try:
            send_result_email_gmail(
                to_email=submission.email,
                name=submission.name,
                total_questions=total_questions,
                correct_answers=correct_count,
                score=total_marks
            )
        except Exception as e:
            print(f"Failed to send email: {e}")

        return SubmissionResultNoCategory(
            email=submission.email,
            name=submission.name,
            total_questions=total_questions,
            correct_answers=correct_count,
            score=total_marks
        )
    finally:
        db.close()

# ---------- Email Sending ----------
def send_result_email_gmail(to_email: str, name: str, total_questions: int, correct_answers: int, score: int):
    sender_email = "prameelarani769@gmail.com"
    sender_password = "cnzb wdwn vkix vprz"  # Gmail App Password

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    subject = "Your Quiz Results"
    body = f"""
    Hello {name},

    Thank you for completing the quiz!

    Total Questions: {total_questions}
    Correct Answers: {correct_answers}
     Score: {score}

    Regards,
    Quiz Team
    """

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, message.as_string())
