from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.database.models import User
from backend.auth.security import hash_password, verify_password

# Defina o tempo de expiração do token caso use JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # exemplo, ajuste conforme necessário

# Função auxiliar para obter usuário pelo email
def get_user_by_email(email: str, db: Session):
    """Retorna um usuário pelo email ou None se não existir."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, name: str, email: str, password: str, is_active:bool):
    """Registra um novo usuário."""
    existing = get_user_by_email(email, db)
    if existing:
        raise HTTPException(status_code=400, detail="Usuário já cadastrado")

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        is_active=is_active
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str):
    """Valida login e retorna token (se usar JWT)."""
    user = get_user_by_email(email, db)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Conta pendente de aprovação")

    # Se estiver usando JWT, implemente a criação do token aqui
    # Exemplo genérico:
    token = f"TOKEN_DE_EXEMPLO_PARA_{user.email}"

    return {"access_token": token, "token_type": "bearer"}

def get_all_users(db: Session):
    """Retorna todos os usuários cadastrados."""
    return db.query(User).all()

def update_user_role_and_status(db: Session, user_id: int, role: str = None, is_active: bool = None):
    """Atualiza o papel (role) e/ou status ativo de um usuário."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if role:
        user.role = role
    if is_active is not None:
        user.is_active = is_active

    db.commit()
    db.refresh(user)
    return user
