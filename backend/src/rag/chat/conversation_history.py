import uuid

from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from sqlalchemy import desc

from backend.database.models import Session as SessionModel

from backend.database.database import Base, SessionLocal, sqlal_engine
from backend.src.llm import LLMClient
from backend.src.utils.logger import setup_logger

logger = setup_logger(__name__ )
class SessionManager:
    """Gerencia o histórico da conversa e fornece acesso ao buffer de memória."""

    def __init__(self):
        Base.metadata.create_all(bind=sqlal_engine)
        self.SessionDB = SessionLocal
        self.sessions = self.load_sessions()

        try:
            self.title_llm = LLMClient().llm
            self.title_prompt = PromptTemplate.from_template(
                "Crie um título curto (máximo 5 palavras) para a seguinte conversa. "
                "Responda APENAS com o título. \n\nPergunta: {question}\n\nTítulo:"
            )
            self.title_chain = self.title_prompt | self.title_llm | StrOutputParser()
        except Exception as e:
            logger.error(f"Erro ao inicializar LLM de títulos: {e}")

        try:
            with sqlal_engine.connect() as conn:
                logger.debug("Conexão bem-sucedida!\n")

        except Exception as e:
            logger.error(f"Erro na conexão: \n{e}")


    def create_session(self, user_id , name:str = None, fixed_context: list = None) -> str:
        session_id = str(uuid.uuid4())[:8]
        session_name = name or "Novo Chat"

        # db= self.SessionDB()
        with self.SessionDB() as db:
            try:
                new_session = SessionModel(
                    id=session_id,
                    name=session_name,
                    user_id=user_id,
                    fixed_context=fixed_context
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

    def get_session_title(self, session_id: str) -> str:
        """Busca o título (nome) atual de uma sessão."""
        with self.SessionDB() as db:
            try:
                session = db.query(SessionModel.name).filter(SessionModel.id == session_id).first()
                return session[0] if session else "Chat"
            except Exception as e:
                logger.error(f"Erro ao buscar título da sessão {session_id}: {e}")
                return "Chat"

    def update_session_title(self, session_id: str, new_title: str):
        """Atualiza o título (nome) de uma sessão existente."""
        with self.SessionDB() as db:
            try:
                session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
                if session:
                    session.name = new_title  # Atualiza o campo 'name'
                    db.commit()
                    logger.info(f"Título da sessão {session_id} atualizado para '{new_title}'")
                else:
                    logger.warning(f"Sessão {session_id} não encontrada para atualizar título.")
            except Exception as e:
                db.rollback()
                logger.error(f"Erro ao atualizar título da sessão {session_id}: {e}")

    def generate_chat_title(self, first_question: str) -> str:
        """Gera um título para o chat usando a primeira pergunta."""
        try:
            title = self.title_chain.invoke({"question": first_question})
            return title.strip().replace('"', '').replace("'", "").replace("Título: ", "")
        except Exception as e:
            logger.error(f"Erro ao gerar título: {e}")
            return "Chat Rápido"

    def get_session_details(self, session_id: str) -> SessionModel:
        with self.SessionDB() as db:
            try:
                session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
                return session
            except Exception as e:
                logger.error(f"Erro ao buscar detalhes da sessão {session_id}: {e}")
                return None

    def list_sessions(self, user_id):
        """Lista todas as sessões criadas."""
        # return self.sessions.keys()
        with self.SessionDB() as db:
            try:
                sessions = db.query(SessionModel).filter(SessionModel.user_id == user_id).order_by(desc(
                    SessionModel.created_at)).all()
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

from backend.database.models import User

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