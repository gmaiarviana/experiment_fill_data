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