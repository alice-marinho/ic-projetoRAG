import enum
import uuid

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import Column, String, Integer, DateTime, func, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
import datetime

from sqlalchemy.orm import DeclarativeBase, relationship


# Base = declarative_base()
class Base(DeclarativeBase):
    pass

class UserRole(str, enum.Enum):
    professor = "professor"
    admin = "admin"
    super_admin = "super_admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(200), nullable=False)

    role = Column(
        Enum(UserRole, native_enum=False),
        nullable=False,
        default=UserRole.professor
    )

    is_active = Column(Boolean, default=False, nullable=False)

    sessions = relationship("Session", back_populates="user")


class Session(Base):
    __tablename__= "sessions"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    fixed_context = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="sessions")

class ParentDocument(Base):
    """Tabela ParentDocument:
    @:var id String
    content: JSONB
    metadata_json: JSONB
    created_at
    updated_at
    """
    __tablename__ = "parent_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(JSONB, nullable=False)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    children = relationship("ChildChunk", back_populates="parent", cascade="all")

class ChildChunk(Base):
    __tablename__ = "child_chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String, ForeignKey("parent_documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(String, nullable=False)
    embedding = Column(VECTOR(768), nullable=False)  # <-- Renomeado
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parent = relationship("ParentDocument", back_populates="children")