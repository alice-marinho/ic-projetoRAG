from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from langchain_postgres import PGEngine
from sqlalchemy.orm import sessionmaker, declarative_base

from .db_config import DATABASE_URL, ASYNC_DATABASE_URL


Base = declarative_base()

#==== comunicação com o banco de dados ====#

### banco vetorial
# pg_engine  = PGEngine.from_connection_string(url=DATABASE_URL)

### outras tabelas
sqlal_engine = create_engine(
    DATABASE_URL, pool_pre_ping=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlal_engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()