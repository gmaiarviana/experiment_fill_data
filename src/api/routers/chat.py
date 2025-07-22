from fastapi import APIRouter, Request, HTTPException
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
async def chat_message(request: Request) -> ChatResponse:
    """Process chat message using ChatService."""
    logger.info("=== INÍCIO: Endpoint /chat/message com ChatService ===")
    
    try:
        # Parse request body
        logger.info(f"Content-Type: {request.headers.get('content-type', 'N/A')}")
        body_bytes = await request.body()
        logger.info(f"Raw body length: {len(body_bytes)} bytes")
        
        try:
            body_text = body_bytes.decode('utf-8')
            logger.info(f"Body decoded as UTF-8: {body_text[:200]}...")
        except UnicodeDecodeError as e:
            logger.error(f"Erro de encoding UTF-8: {e}")
            raise HTTPException(status_code=400, detail="Invalid UTF-8 encoding in request body")
        
        try:
            body_json = json.loads(body_text)
            logger.info(f"JSON parsed successfully: {json.dumps(body_json, ensure_ascii=False)[:200]}...")
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao fazer parse do JSON: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        
        try:
            chat_request = ChatRequest(**body_json)
            logger.info(f"ChatRequest validado com sucesso: message='{chat_request.message[:50]}...'")
        except Exception as e:
            logger.error(f"Erro na validação Pydantic: {e}")
            raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
        
        # Get session ID from request
        session_id = body_json.get("session_id")
        
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