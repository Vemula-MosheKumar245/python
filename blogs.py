from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from typing import List

# DATABASE CONFIG
DATABASE_URL = "postgresql+psycopg2://postgres:root@localhost/Linda"

engine = create_engine(DATABASE_URL)  # ✅ FIXED: Removed SQLite-only config
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# MODELS
class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    blogs = relationship("Blog", back_populates="author", cascade="all, delete")

class Blog(Base):
    __tablename__ = "blogs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("authors.id"))

    author = relationship("Author", back_populates="blogs")

# SCHEMAS
class BlogBase(BaseModel):
    title: str
    body: str

class BlogCreate(BlogBase):
    pass

class BlogUpdate(BlogBase):
    pass

class BlogResponse(BlogBase):
    id: int
    class Config:
        orm_mode = True

class AuthorCreate(BaseModel):
    name: str
    password: str

class AuthorResponse(BaseModel):
    id: int
    name: str
    blogs: List[BlogResponse] = []
    class Config:
        orm_mode = True

# CREATE TABLES
Base.metadata.create_all(bind=engine)

# FASTAPI INSTANCE
app = FastAPI()

# DEPENDENCY
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ENDPOINTS

@app.post("/authors/", response_model=AuthorResponse)
def create_author(author: AuthorCreate, db: Session = Depends(get_db)):
    existing = db.query(Author).filter(Author.name == author.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Author already exists")
    new_author = Author(name=author.name, password=author.password)
    db.add(new_author)
    db.commit()
    db.refresh(new_author)
    return new_author

@app.post("/authors/{author_name}/blogs/", response_model=BlogResponse)
def create_blog(author_name: str, blog: BlogCreate, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.name == author_name).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    existing_blog = db.query(Blog).filter(
        Blog.author_id == author.id,
        Blog.title == blog.title
    ).first()

    if existing_blog:
        raise HTTPException(status_code=400, detail="Blog title already exists for this author")
    new_blog = Blog(title=blog.title, body=blog.body, author_id=author.id)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog

@app.get("/authors/{author_name}/blogs/", response_model=AuthorResponse)
def get_author_blogs(author_name: str, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.name == author_name).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author

@app.put("/authors/{author_name}/blogs/{blog_id}/", response_model=BlogResponse)
def update_blog(author_name: str, blog_id: int, blog_update: BlogUpdate, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.name == author_name).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    blog = db.query(Blog).filter(Blog.id == blog_id, Blog.author_id == author.id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found or does not belong to the author")
    blog.title = blog_update.title
    blog.body = blog_update.body
    db.commit()
    db.refresh(blog)
    return blog

@app.delete("/authors/{author_name}/blogs/{blog_id}/")
def delete_blog(author_name: str, blog_id: int, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.name == author_name).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    blog = db.query(Blog).filter(Blog.id == blog_id, Blog.author_id == author.id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found or does not belong to the author")
    db.delete(blog)
    db.commit()
    return {"message": f"Blog with ID {blog_id} deleted successfully."}

@app.delete("/authors/{author_name}/")
def delete_author(author_name: str, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.name == author_name).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    db.delete(author)
    db.commit()
    return {"message": f"Author '{author_name}' and all their blogs deleted successfully."}
