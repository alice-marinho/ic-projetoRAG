import uuid
from typing import Dict

from langchain_community.chat_message_histories import SQLChatMessageHistory
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Session as SessionModel, Base

from database.base import Base
from database.db_config import DATABASE_URL
from utils.logger import setup_logger


# from rag.generator import get_session_history

logger = setup_logger(__name__ )
class SessionManager:
    """Gerencia o histórico da conversa e fornece acesso ao buffer de memória."""

    def __init__(self, db_url = DATABASE_URL):

        logger = setup_logger(__name__)
        # engine cria conexão, envia comandos e gerencia o pool de conexões
        try:
            self.engine = create_engine(db_url)
            with self.engine.connect() as conn:
                logger.debug("Conexão bem-sucedida!\n")
        except Exception as e:
            logger.error(f"Erro na conexão: \n{e}")

        Base.metadata.create_all(self.engine)
        self.SessionDB = sessionmaker(bind=self.engine)

        self.sessions = self.load_sessions()

        # Guarda as memórias por ID
        # self.sessions = {}

    def create_session(self, name:str = None) -> str:
        session_id = str(uuid.uuid4())[:8]
        session_name = name or f"Sessão {len(self.sessions)+1}"

        db= self.SessionDB()
        db.add(SessionModel(id=session_id, name=session_name))
        db.commit() # insere no bd
        db.close() # fecha sessão

        self.sessions[session_id] = session_name


        # get_session_history(session_id)
        # self.get_session(session_id)
        # self.sessions[session_id] = {
        #     "name": name or f"Sessão {len(self.sessions) + 1}",
        #     "history": self.get_session(session_id)
        # }
        return session_id

    #@staticmethod
    def get_session(self, session_id):
        """Retorna a sessão existente ou cria uma nova."""
        return SQLChatMessageHistory(
            session_id=session_id,
            # connection="sqlite:///chat_history.db"
            # connection=str(self.engine.url),
            connection=self.engine.url.render_as_string(hide_password=False),
            table_name="message_store"
        )

    def list_sessions(self):
        """Lista todas as sessões criadas."""
        # return self.sessions.keys()
        return self.sessions

    def delete_all_sessions(self):
        # db = self.SessionDB()
        with self.SessionDB as db:
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
        db = self.SessionDB()
        db.query(SessionModel).filter(SessionModel.id == session_id).delete()
        # db.query(Message).filter(Message.session.id == session_id).delete()
        db.commit()
        db.close()
        self.sessions.pop(session_id, None)

    def load_sessions(self):
        """Carrega todas as sessões já criadas no banco"""
        db = self.SessionDB()
        result = db.query(SessionModel).all()
        db.close()
        return{s.id: s.name for s in result}
