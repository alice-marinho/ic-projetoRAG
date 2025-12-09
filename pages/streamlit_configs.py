import streamlit as st
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


@st.cache_data(show_spinner=False, ttl=300)
def fetch_sessions_cached(user_id):
    """
    Função compartilhada para buscar sessões.
    Pode ser importada pelo Login (para aquecer) e pelo Chat (para ler).
    """
    try:
        from backend.src.rag.chat.conversation_history import SessionManager

        manager = SessionManager()
        basic_sessions = manager.list_sessions(user_id=user_id)
        enriched_list = []
        for session_id, title in basic_sessions.items():
            try:
                session_obj = manager.get_session(session_id)
                created_at = getattr(session_obj, 'created_at', None)

                enriched_list.append({
                    "id": session_id,
                    "name": title,
                    "created_at": created_at
                })
            except Exception:
                continue
        sorted_list = sorted(
            enriched_list,
            key=lambda x: x['created_at'] if x['created_at'] else "",
            reverse=True
        )
        return sorted_list
    except Exception as e:
        print(f"⚠️ Erro no cache manager: {e}")
        return {}


@st.cache_data(show_spinner=False, ttl=300)
def fetch_chat_history_cached(session_id):
    """
    Busca as mensagens de um chat específico e guarda na RAM.
    Isso faz a troca de chats ser instantânea, sem ir no banco toda hora.
    """
    try:
        from backend.src.rag.chat.conversation_history import SessionManager
        manager = SessionManager()

        session_obj = manager.get_session(session_id)

        return session_obj.messages
    except Exception as e:
        print(f"Erro no cache de mensagens: {e}")
        return []