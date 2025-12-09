from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.database import get_db
from ..auth.user_service import create_user, login_user
# from ..auth.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(name: str, email: str, password: str, db: Session = Depends(get_db)):
    return create_user(db, name, email, password)

@router.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    return login_user(db, email, password)

# @router.get("/me")
# def get_me(current_user = Depends(get_current_user)):
#     return {"id": current_user.id, "email": current_user.email, "name": current_user.name}
