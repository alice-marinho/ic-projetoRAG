from argon2 import hash_password
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
def hash_password(password: str) -> str:
    """Gera hash seguro para senha."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha bate com o hash."""
    return pwd_context.verify(plain_password, hashed_password)