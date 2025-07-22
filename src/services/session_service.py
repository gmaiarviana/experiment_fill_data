from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SessionService:
    """
    Service responsável por gerenciar o contexto de sessão das conversas.
    Centraliza criação, recuperação, atualização e deleção de sessões.
    """
    def __init__(self):
        # Pode ser substituído por persistência real futuramente
        self._sessions = {}

    def create_session(self, session_id: str, initial_context: dict = None) -> dict:
        context = initial_context or {
            "session_start": None,
            "conversation_history": [],
            "extracted_data": {},
            "total_confidence": 0.0,
            "confidence_count": 0,
            "average_confidence": 0.0
        }
        self._sessions[session_id] = context
        return context

    def get_session(self, session_id: str) -> dict:
        return self._sessions.get(session_id)

    def update_session(self, session_id: str, context: dict) -> None:
        self._sessions[session_id] = context

    def delete_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]

    def list_sessions(self) -> dict:
        return self._sessions.copy() 
    
    def cleanup_old_sessions(self):
        """Remove sessions older than 24 hours"""
        current_time = datetime.utcnow()
        sessions_to_remove = []
        
        for session_id, context in self._sessions.items():
            session_start = context.get("session_start")
            if session_start:
                try:
                    start_time = datetime.fromisoformat(session_start)
                    if (current_time - start_time).total_seconds() > 86400:  # 24 hours
                        sessions_to_remove.append(session_id)
                except (ValueError, TypeError):
                    # Invalid timestamp, remove session
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self._sessions[session_id]
            logger.info(f"Sessão expirada removida: {session_id}")
            
        return len(sessions_to_remove)