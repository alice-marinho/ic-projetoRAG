from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

from sqlalchemy.orm import DeclarativeBase

# Base = declarative_base()
class Base(DeclarativeBase):
    pass

class Session(Base):
    __tablename__= "sessions"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
