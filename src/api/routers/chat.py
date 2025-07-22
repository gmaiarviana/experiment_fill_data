from fastapi import APIRouter, HTTPException
from src.api.schemas.chat import ChatRequest, ChatResponse
from datetime import datetime
from typing import Dict, Any
import uuid
import json
import logging

from src.core.container import get_chat_service
from src.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat/message", response_model=ChatResponse)
async def chat_message(chat_request: ChatRequest) -> ChatResponse:
    """Process chat message using ChatService."""
    logger.info("=== INÍCIO: Endpoint /chat/message com ChatService ===")
    
    try:
        logger.info(f"ChatRequest recebido: message='{chat_request.message[:50]}...'")
        
        # Get session ID from request
        session_id = chat_request.session_id
        
        # Process message using ChatService
        chat_service = get_chat_service()
        result = await chat_service.process_message(chat_request.message, session_id)
        
        # Convert result to ChatResponse
        response = ChatResponse(
            response=result.get("response", "Desculpe, não consegui processar sua mensagem."),
            session_id=result.get("session_id", str(uuid.uuid4())),
            timestamp=result.get("timestamp", datetime.utcnow()),
            action=result.get("action", "unknown"),
            extracted_data=result.get("extracted_data", {}),
            confidence=result.get("confidence", 0.0),
            next_questions=result.get("next_questions", []),
            consultation_id=result.get("consultation_id"),
            persistence_status=result.get("persistence_status", "not_applicable")
        )
        
        logger.info("=== FIM: Endpoint /chat/message - Sucesso ===")
        return response
        
    except HTTPException:
        logger.error("=== FIM: Endpoint /chat/message - HTTPException ===")
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao processar chat message: {e}")
        logger.error("=== FIM: Endpoint /chat/message - Erro ===")
        return ChatResponse(
            response=f"Ocorreu um erro ao processar sua mensagem: {str(e)}",
            session_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow()
        ) 