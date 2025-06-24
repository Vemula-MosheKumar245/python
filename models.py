from sqlalchemy import column,String,Integer
from database import Base

class Student(Base):
    id = Column(Integer,primary_key=True)
    name = Column(String)
    age = Column(Integer)