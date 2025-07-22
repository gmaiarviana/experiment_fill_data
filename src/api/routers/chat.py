from fastapi import APIRouter, Request, HTTPException
from src.api.schemas.chat import ChatRequest, ChatResponse
from datetime import datetime
from typing import Dict, Any
import uuid
import json
import logging

from src.core.container import get_openai_client, get_consultation_service
from src.core.reasoning.reasoning_coordinator import ReasoningCoordinator

# Sessions dict deve ser importado do main ou, preferencialmente, movido para um módulo compartilhado
try:
    from src.api.main import sessions, cleanup_old_sessions
except ImportError:
    # Fallback para evitar erro em import circular durante testes
    sessions = {}
    def cleanup_old_sessions():
        pass

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat/message", response_model=ChatResponse)
async def chat_message(request: Request) -> ChatResponse:
    logger.info("=== INÍCIO: Endpoint /chat/message com ReasoningCoordinator ===")
    try:
        logger.info(f"Content-Type: {request.headers.get('content-type', 'N/A')}")
        logger.info(f"Content-Length: {request.headers.get('content-length', 'N/A')}")
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
        session_id = body_json.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
        elif not session_id.startswith("session_"):
            pass
        else:
            session_id = str(uuid.uuid4())
        if session_id not in sessions:
            sessions[session_id] = {
                "session_start": datetime.utcnow().isoformat(),
                "conversation_history": [],
                "extracted_data": {},
                "total_confidence": 0.0,
                "confidence_count": 0,
                "average_confidence": 0.0
            }
            logger.info(f"Nova sessão criada: {session_id}")
        else:
            logger.info(f"Sessão existente recuperada: {session_id}")
        context = sessions[session_id]
        if len(sessions) % 10 == 0:
            cleanup_old_sessions()
        reasoning_engine = ReasoningCoordinator()
        if reasoning_engine is None:
            logger.warning("Reasoning Engine não disponível, usando fallback OpenAI")
            openai_client = get_openai_client()
            if openai_client is None:
                return ChatResponse(
                    response="Desculpe, o serviço de IA não está disponível no momento. Tente novamente mais tarde.",
                    session_id=session_id,
                    timestamp=datetime.utcnow()
                )
            ai_response = await openai_client.chat_completion(chat_request.message)
            response = ChatResponse(
                response=ai_response,
                session_id=session_id,
                timestamp=datetime.utcnow()
            )
        else:
            logger.info(f"Processando mensagem com ReasoningCoordinator: '{chat_request.message[:50]}...'")
            try:
                result = await reasoning_engine.process_message(chat_request.message, context)
                logger.info("ReasoningCoordinator processamento concluído com sucesso")
                sessions[session_id] = context
                action = result.get("action", "unknown")
                response_text = result.get("response", "Desculpe, não consegui processar sua mensagem.")
                extracted_data_raw = result.get("extracted_data", {})
                confidence = result.get("confidence", 0.0)
                logger.info(f"Raw extracted_data from reasoning engine: {extracted_data_raw}")
                extracted_data = extracted_data_raw.copy()
                logger.info(f"ReasoningCoordinator resultado - Ação: {action}, Confidence: {confidence:.2f}")
                if extracted_data:
                    logger.info(f"Dados extraídos: {list(extracted_data.keys())}")
                consultation_id = None
                persistence_status = "not_applicable"
                consultation_service = get_consultation_service()
                if extracted_data and action in ["extract", "confirm", "complete"] and consultation_service is not None:
                    try:
                        logger.info(f"Extracted data for persistence: {extracted_data}")
                        logger.info(f"Action: {action}, Consultation service available: {consultation_service is not None}")
                        logger.info("Tentando persistir dados extraídos via ConsultationService")
                        persistence_result = await consultation_service.process_and_persist(
                            chat_request.message, 
                            session_id,
                            extracted_data.get("normalized_data", {})
                        )
                        if persistence_result.get("success", False):
                            consultation_id = persistence_result.get("consultation_id")
                            persistence_status = "success"
                            logger.info(f"✅ Consulta persistida com sucesso - ID: {consultation_id}")
                            if action == "extract":
                                response_text += f"\n\n✅ Consulta registrada com sucesso! (ID: {consultation_id})"
                            elif action == "confirm":
                                response_text += f"\n\n✅ Consulta confirmada e salva! (ID: {consultation_id})"
                            elif action == "complete":
                                response_text += f"\n\n✅ Consulta completa registrada com sucesso! (ID: {consultation_id})"
                        else:
                            persistence_status = "failed"
                            persistence_errors = persistence_result.get("errors", [])
                            logger.warning(f"❌ Falha na persistência: {persistence_errors}")
                            response_text += f"\n\n⚠️ Não foi possível salvar a consulta: {', '.join(persistence_errors)}"
                    except Exception as e:
                        persistence_status = "error"
                        logger.error(f"Erro durante persistência: {str(e)}")
                        response_text += f"\n\n⚠️ Erro ao salvar consulta: {str(e)}"
                response = ChatResponse(
                    response=response_text,
                    session_id=session_id,
                    timestamp=datetime.utcnow(),
                    action=action,
                    extracted_data=extracted_data,
                    confidence=confidence,
                    next_questions=result.get("next_questions", []),
                    consultation_id=consultation_id,
                    persistence_status=persistence_status
                )
                logger.info(f"Reasoning data - Action: {action}, Confidence: {confidence}, Data: {extracted_data}, Persistence: {persistence_status}, Consultation ID: {consultation_id}")
            except Exception as e:
                logger.error(f"Erro no ReasoningCoordinator: {str(e)}")
                openai_client = get_openai_client()
                if openai_client is not None:
                    logger.info("Usando fallback OpenAI devido a erro no ReasoningCoordinator")
                    ai_response = await openai_client.chat_completion(chat_request.message)
                    response = ChatResponse(
                        response=ai_response,
                        session_id=session_id,
                        timestamp=datetime.utcnow()
                    )
                else:
                    response = ChatResponse(
                        response=f"Ocorreu um erro ao processar sua mensagem: {str(e)}",
                        session_id=session_id,
                        timestamp=datetime.utcnow()
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