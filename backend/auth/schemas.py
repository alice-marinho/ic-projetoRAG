from pydantic import BaseModel
from backend.database.models import UserRole  # Precisamos do Enum


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserPublic(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class UserAdminView(UserPublic):
    password_hash: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    role: UserRole
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatRequest(BaseModel):
    question: str
    session_id: str

class ChatResponse(BaseModel):
    answer: str