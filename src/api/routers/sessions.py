from fastapi import APIRouter, HTTPException
from src.core.reasoning.reasoning_coordinator import ReasoningCoordinator
from datetime import datetime
import logging

# Sessions dict deve ser importado do main ou, preferencialmente, movido para um módulo compartilhado
try:
    from src.api.main import sessions
except ImportError:
    sessions = {}

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get session information and context"""
    logger.info(f"=== INÍCIO: Endpoint /sessions/{{session_id}} ===")
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        context = sessions[session_id]
        reasoning_engine = ReasoningCoordinator()
        if reasoning_engine:
            summary = reasoning_engine.get_context_summary(context)
        else:
            summary = {
                "total_messages": len(context.get("conversation_history", [])),
                "extracted_fields": list(context.get("extracted_data", {}).keys()),
                "data_completeness": 0.0,
                "last_action": "unknown"
            }
        response = {
            "session_id": session_id,
            "session_start": context.get("session_start"),
            "total_messages": summary["total_messages"],
            "extracted_fields": summary["extracted_fields"],
            "data_completeness": summary["data_completeness"],
            "last_action": summary["last_action"],
            "average_confidence": context.get("average_confidence", 0.0),
            "conversation_history": context.get("conversation_history", [])
        }
        logger.info(f"=== FIM: Endpoint /sessions/{{session_id}} - Sucesso ===")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter informações da sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    logger.info(f"=== INÍCIO: Endpoint DELETE /sessions/{{session_id}} ===")
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        del sessions[session_id]
        logger.info(f"Sessão removida: {session_id}")
        logger.info(f"=== FIM: Endpoint DELETE /sessions/{{session_id}} - Sucesso ===")
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    logger.info("=== INÍCIO: Endpoint /sessions ===")
    try:
        session_list = []
        for session_id, context in sessions.items():
            session_info = {
                "session_id": session_id,
                "session_start": context.get("session_start"),
                "total_messages": len(context.get("conversation_history", [])),
                "extracted_fields": list(context.get("extracted_data", {}).keys()),
                "average_confidence": context.get("average_confidence", 0.0)
            }
            session_list.append(session_info)
        logger.info(f"=== FIM: Endpoint /sessions - {len(session_list)} sessões ===")
        return {"sessions": session_list, "total": len(session_list)}
    except Exception as e:
        logger.error(f"Erro ao listar sessões: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 