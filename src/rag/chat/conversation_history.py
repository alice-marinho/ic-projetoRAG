import uuid
from typing import Dict

from langchain_community.chat_message_histories import SQLChatMessageHistory
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.coercions import expect

from database.models import User, Session as SessionModel

from database.database import Base, SessionLocal, sqlal_engine
from database.db_config import DATABASE_URL, DATABASE_URL_TEST
from utils.logger import setup_logger
import streamlit as st


# from rag.generator import get_session_history

logger = setup_logger(__name__ )
class SessionManager:
    """Gerencia o histórico da conversa e fornece acesso ao buffer de memória."""

    def __init__(self):
        Base.metadata.create_all(bind=sqlal_engine)
        self.SessionDB = SessionLocal
        self.sessions = self.load_sessions()
        try:
            with sqlal_engine.connect() as conn:
                logger.debug("Conexão bem-sucedida!\n")

        except Exception as e:
            logger.error(f"Erro na conexão: \n{e}")

        # with self.SessionDB as db:
        #     user = db.query(User).filter_by(email="test_user@example.com").first()
        #     if not user:
        #         user = User(
        #             name="Usuário Teste",
        #             email="test_user@example.com",
        #             password_hash="fake_hash"
        #         )
        #         db.add(user)
        #         db.commit()
        #         db.refresh(user)
        #
        #     self.test_user_id = user.id


    def create_session(self, user_id , name:str = None) -> str:
        session_id = str(uuid.uuid4())[:8]
        session_name = name or f"Sessão {len(self.sessions)+1}"

        # db= self.SessionDB()
        with self.SessionDB() as db:
            try:
                count = db.query(SessionModel).filter(SessionModel.user_id == user_id).count()
                session_name = name or f"Sessão {count + 1}"

                new_session = SessionModel(
                    id=session_id,
                    name=session_name,
                    user_id=user_id
                )

                db.add(new_session)
                db.commit()
                logger.info(f"Sessão {session_id} criada para o usuário {user_id}.")
                return session_id
            except Exception as e:
                db.rollback()
                logger.error(f"Erro ao criar sessão: {e}")
                raise

    #@staticmethod
    def get_session(self, session_id):
        """Retorna a sessão existente ou cria uma nova."""
        return SQLChatMessageHistory(
            session_id=session_id,
            connection=sqlal_engine.url.render_as_string(hide_password=False),
            table_name="message_store"
        )

    def list_sessions(self, user_id):
        """Lista todas as sessões criadas."""
        # return self.sessions.keys()
        with self.SessionDB() as db:
            try:
                sessions = db.query(SessionModel).filter(SessionModel.user_id == user_id).all()
                return {s.id: s.name for s in sessions}
            except Exception as e:
                logger.error(f"Erro ao carregar sessões do usuário {user_id}: {e}")
                return {}

    def delete_all_sessions(self):
        # db = self.SessionDB()
        with self.SessionDB() as db:
            try:
                num_deleted = db.query(SessionModel).delete()
                db.commit()
                logger.debug(f"{num_deleted} sessões foram excluídas")
            except Exception as e:
                logger.error(f"Erro ao excluir sessões.\n {e}")
                db.rollback()
                raise


    def delete_session(self, session_id: str):
        """Remove uma sessão específica."""
        with self.SessionDB() as db:
            try:
                db.query(SessionModel).filter(SessionModel.id == session_id).delete()
                db.commit()
                self.sessions.pop(session_id, None)
                logger.debug(f"Sessão {session_id} removida.")
            except Exception as e:
                db.rollback()
                logger.error(f"Erro ao remover sessão {session_id}: {e}")


    def load_sessions(self):
        """Carrega todas as sessões já criadas no banco"""
        with self.SessionDB() as db:
            try:
                result = db.query(SessionModel).all()
                return{s.id: s.name for s in result}
            except Exception as e:
                logger.error(f"Erro ao carregar todas as sessões: {e}")


session_manager = SessionManager()

from database.models import User

def get_test_user():
    """Retorna o ID do usuário fixo de teste"""

    with session_manager.SessionDB() as db:
        user = db.query(User).filter_by(email="test_user@example.com").first()
        if not user:
            user = User(
                name="Test User",
                email="test_user@example.com",
                password_hash="fake_hash_for_testing"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Usuário de teste criado: {user.id}")
        return user.id

# ID fixo para testes
TEST_USER_ID = get_test_user()