from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.schemas.chat import ChatRequest, ChatResponse, EntityExtractionRequest, EntityExtractionResponse, ValidationRequest, ValidationResponse
from src.api.routers.system import router as system_router
from src.core.openai_client import OpenAIClient
from src.core.entity_extraction import EntityExtractor
from src.core.reasoning_engine import ReasoningEngine
from src.core.data_normalizer import normalize_consulta_data, normalize_extracted_entities
from src.core.logging import setup_logging
from src.core.config import get_settings
from src.services.consultation_service import ConsultationService
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
import json

# Get centralized settings
settings = get_settings()

# Setup logging with configured log level
logger = setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

logger.info("✅ FastAPI app criada - main.py executando")

# Include routers
app.include_router(system_router)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5678", 
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
try:
    openai_client = OpenAIClient()
    logger.info("OpenAI client inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar OpenAI client: {e}")
    openai_client = None

# Initialize Entity Extractor
try:
    entity_extractor = EntityExtractor()
    logger.info("Entity Extractor inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar Entity Extractor: {e}")
    entity_extractor = None

# Initialize Reasoning Engine
try:
    reasoning_engine = ReasoningEngine()
    logger.info("Reasoning Engine inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar Reasoning Engine: {e}")
    reasoning_engine = None

# Initialize Consultation Service
try:
    consultation_service = ConsultationService()
    logger.info("Consultation Service inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar Consultation Service: {e}")
    consultation_service = None

# Global session management
sessions: Dict[str, Dict[str, Any]] = {}


def cleanup_old_sessions():
    """Remove sessions older than 24 hours"""
    current_time = datetime.utcnow()
    sessions_to_remove = []
    
    for session_id, context in sessions.items():
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
        del sessions[session_id]
        logger.info(f"Sessão expirada removida: {session_id}")


@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint acessado")
    return {
        "message": "Data Structuring Agent API",
        "status": "running"
    }


@app.post("/chat/message")
async def chat_message(request: Request) -> ChatResponse:
    """Chat message endpoint with ReasoningEngine integration and session management"""
    logger.info("=== INÍCIO: Endpoint /chat/message com ReasoningEngine ===")
    
    try:
        # Log request details
        logger.info(f"Content-Type: {request.headers.get('content-type', 'N/A')}")
        logger.info(f"Content-Length: {request.headers.get('content-length', 'N/A')}")
        
        # Read raw body for debugging
        body_bytes = await request.body()
        logger.info(f"Raw body length: {len(body_bytes)} bytes")
        
        # Try to decode as UTF-8
        try:
            body_text = body_bytes.decode('utf-8')
            logger.info(f"Body decoded as UTF-8: {body_text[:200]}...")
        except UnicodeDecodeError as e:
            logger.error(f"Erro de encoding UTF-8: {e}")
            raise HTTPException(status_code=400, detail="Invalid UTF-8 encoding in request body")
        
        # Parse JSON
        try:
            body_json = json.loads(body_text)
            logger.info(f"JSON parsed successfully: {json.dumps(body_json, ensure_ascii=False)[:200]}...")
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao fazer parse do JSON: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        
        # Validate with Pydantic
        try:
            chat_request = ChatRequest(**body_json)
            logger.info(f"ChatRequest validado com sucesso: message='{chat_request.message[:50]}...'")
        except Exception as e:
            logger.error(f"Erro na validação Pydantic: {e}")
            raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
        
        # Generate session ID if not provided in request
        session_id = body_json.get("session_id", str(uuid.uuid4()))
        
        # Get or create session context
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
        
        # Cleanup old sessions periodically
        if len(sessions) % 10 == 0:  # Every 10 requests
            cleanup_old_sessions()
        
        # Process message with ReasoningEngine
        if reasoning_engine is None:
            logger.warning("Reasoning Engine não disponível, usando fallback OpenAI")
            if openai_client is None:
                return ChatResponse(
                    response="Desculpe, o serviço de IA não está disponível no momento. Tente novamente mais tarde.",
                    session_id=session_id,
                    timestamp=datetime.utcnow()
                )
            
            # Fallback to OpenAI
            ai_response = await openai_client.chat_completion(chat_request.message)
            response = ChatResponse(
                response=ai_response,
                session_id=session_id,
                timestamp=datetime.utcnow()
            )
        else:
            # Use ReasoningEngine
            logger.info(f"Processando mensagem com ReasoningEngine: '{chat_request.message[:50]}...'")
            
            try:
                result = await reasoning_engine.process_message(chat_request.message, context)
                logger.info("ReasoningEngine processamento concluído com sucesso")
                
                # Update session context
                sessions[session_id] = context
                
                # Extract response components
                action = result.get("action", "unknown")
                response_text = result.get("response", "Desculpe, não consegui processar sua mensagem.")
                extracted_data = result.get("data", {})
                confidence = result.get("confidence", 0.0)
                
                # Log reasoning results
                logger.info(f"ReasoningEngine resultado - Ação: {action}, Confidence: {confidence:.2f}")
                if extracted_data:
                    logger.info(f"Dados extraídos: {list(extracted_data.keys())}")
                
                # INTEGRAÇÃO COM PERSISTÊNCIA - Funcionalidade 3.6
                consultation_id = None
                persistence_status = "not_applicable"
                
                # Se temos dados extraídos e ação é "extract", "confirm" ou "complete", tentar persistir
                if extracted_data and action in ["extract", "confirm", "complete"] and consultation_service is not None:
                    try:
                        logger.info("Tentando persistir dados extraídos via ConsultationService")
                        
                        # Processar e persistir dados
                        persistence_result = await consultation_service.process_and_persist(
                            chat_request.message, 
                            session_id
                        )
                        
                        if persistence_result.get("success", False):
                            consultation_id = persistence_result.get("consultation_id")
                            persistence_status = "success"
                            logger.info(f"✅ Consulta persistida com sucesso - ID: {consultation_id}")
                            
                            # Atualizar response com confirmação de persistência
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
                            
                            # Adicionar informação sobre falha na persistência
                            response_text += f"\n\n⚠️ Não foi possível salvar a consulta: {', '.join(persistence_errors)}"
                            
                    except Exception as e:
                        persistence_status = "error"
                        logger.error(f"Erro durante persistência: {str(e)}")
                        response_text += f"\n\n⚠️ Erro ao salvar consulta: {str(e)}"
                
                # Create enhanced response with ReasoningEngine data and persistence info
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
                
                # Log reasoning results with persistence info
                logger.info(f"Reasoning data - Action: {action}, Confidence: {confidence}, Data: {extracted_data}, Persistence: {persistence_status}, Consultation ID: {consultation_id}")
                
            except Exception as e:
                logger.error(f"Erro no ReasoningEngine: {str(e)}")
                # Fallback to OpenAI if ReasoningEngine fails
                if openai_client is not None:
                    logger.info("Usando fallback OpenAI devido a erro no ReasoningEngine")
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


@app.post("/extract/entities")
async def extract_entities(request: Request) -> EntityExtractionResponse:
    """Entity extraction endpoint with detailed logging and validation"""
    logger.info("=== INÍCIO: Endpoint /extract/entities ===")
    
    try:
        # Log request details
        logger.info(f"Content-Type: {request.headers.get('content-type', 'N/A')}")
        logger.info(f"Content-Length: {request.headers.get('content-length', 'N/A')}")
        
        # Read raw body for debugging
        body_bytes = await request.body()
        logger.info(f"Raw body length: {len(body_bytes)} bytes")
        
        # Try to decode as UTF-8
        try:
            body_text = body_bytes.decode('utf-8')
            logger.info(f"Body decoded as UTF-8: {body_text[:200]}...")
        except UnicodeDecodeError as e:
            logger.error(f"Erro de encoding UTF-8: {e}")
            raise HTTPException(status_code=400, detail="Invalid UTF-8 encoding in request body")
        
        # Parse JSON
        try:
            body_json = json.loads(body_text)
            logger.info(f"JSON parsed successfully: {json.dumps(body_json, ensure_ascii=False)[:200]}...")
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao fazer parse do JSON: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        
        # Validate with Pydantic using specific schema
        try:
            extraction_request = EntityExtractionRequest(**body_json)
            logger.info(f"EntityExtractionRequest validado com sucesso: message='{extraction_request.message[:50]}...'")
        except Exception as e:
            logger.error(f"Erro na validação Pydantic: {e}")
            raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
        
        # Process entity extraction
        if entity_extractor is None:
            logger.warning("Entity Extractor não disponível")
            return EntityExtractionResponse(
                success=False,
                error="Serviço de extração não está disponível no momento"
            )
        
        # Extract entities using the entity extractor
        result = await entity_extractor.extract_consulta_entities(extraction_request.message)
        logger.info("Extração de entidades realizada com sucesso")
        
        # Log the complete result for debugging
        logger.info(f"Result completo: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # Convert result to EntityExtractionResponse
        if isinstance(result, dict) and result.get("success", False):
            response = EntityExtractionResponse(
                success=True,
                entities=result.get("extracted_data"),  # Mapeia extracted_data → entities
                confidence_score=result.get("confidence_score"),
                missing_fields=result.get("missing_fields"),
                suggested_questions=result.get("suggested_questions"),
                is_complete=result.get("is_complete"),
                timestamp=datetime.utcnow()
            )
            logger.info(f"Response mapeada: success={response.success}, entities_keys={list(response.entities.keys()) if response.entities else None}, confidence={response.confidence_score}")
        else:
            response = EntityExtractionResponse(
                success=False,
                error=result.get("error", "Erro desconhecido na extração") if isinstance(result, dict) else str(result)
            )
            logger.info(f"Response de erro: {response.error}")
        
        logger.info("=== FIM: Endpoint /extract/entities - Sucesso ===")
        return response
        
    except HTTPException:
        logger.error("=== FIM: Endpoint /extract/entities - HTTPException ===")
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao extrair entidades: {e}")
        logger.error("=== FIM: Endpoint /extract/entities - Erro ===")
        return EntityExtractionResponse(
            success=False,
            error=f"Erro ao processar extração: {str(e)}"
        )


@app.post("/validate")
async def validate_data(request: Request) -> ValidationResponse:
    """Validation endpoint with detailed logging and error handling"""
    logger.info("=== INÍCIO: Endpoint /validate ===")
    
    try:
        # Log request details
        logger.info(f"Content-Type: {request.headers.get('content-type', 'N/A')}")
        logger.info(f"Content-Length: {request.headers.get('content-length', 'N/A')}")
        
        # Read raw body for debugging
        body_bytes = await request.body()
        logger.info(f"Raw body length: {len(body_bytes)} bytes")
        
        # Try to decode as UTF-8
        try:
            body_text = body_bytes.decode('utf-8')
            logger.info(f"Body decoded as UTF-8: {body_text[:200]}...")
        except UnicodeDecodeError as e:
            logger.error(f"Erro de encoding UTF-8: {e}")
            return ValidationResponse(
                success=False,
                normalized_data={},
                validation_errors=[f"Invalid UTF-8 encoding in request body: {str(e)}"],
                confidence_score=0.0
            )
        
        # Parse JSON
        try:
            body_json = json.loads(body_text)
            logger.info(f"JSON parsed successfully: {json.dumps(body_json, ensure_ascii=False)[:200]}...")
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao fazer parse do JSON: {e}")
            return ValidationResponse(
                success=False,
                normalized_data={},
                validation_errors=[f"Invalid JSON format: {str(e)}"],
                confidence_score=0.0
            )
        
        # Validate with Pydantic
        try:
            validation_request = ValidationRequest(**body_json)
            logger.info(f"ValidationRequest validado com sucesso: domain='{validation_request.domain}', data_keys={list(validation_request.data.keys()) if validation_request.data else None}")
        except Exception as e:
            logger.error(f"Erro na validação Pydantic: {e}")
            return ValidationResponse(
                success=False,
                normalized_data={},
                validation_errors=[f"Validation error: {str(e)}"],
                confidence_score=0.0
            )
        
        # Process validation based on domain
        try:
            if validation_request.domain == "consulta":
                logger.info("Usando normalize_consulta_data para domínio 'consulta'")
                result = normalize_consulta_data(validation_request.data)
            else:
                logger.info(f"Usando normalize_extracted_entities para domínio '{validation_request.domain}'")
                result = normalize_extracted_entities(validation_request.data, validation_request.domain)
            
            logger.info("Validação realizada com sucesso")
            logger.info(f"Result completo: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Extract data from result
            normalized_data = result.get("normalized_data", {}) if validation_request.domain == "consulta" else result.get("normalized_entities", {})
            validation_errors = result.get("validation_errors", [])
            confidence_score = result.get("confidence_score", 0.0)
            
            # Determine success based on confidence score and errors
            success = confidence_score > 0.0 and len(validation_errors) == 0
            
            response = ValidationResponse(
                success=success,
                normalized_data=normalized_data,
                validation_errors=validation_errors,
                confidence_score=confidence_score
            )
            
            logger.info(f"Response criada: success={response.success}, confidence={response.confidence_score}, errors_count={len(response.validation_errors)}")
            
        except Exception as e:
            logger.error(f"Erro durante a normalização: {e}")
            return ValidationResponse(
                success=False,
                normalized_data={},
                validation_errors=[f"Erro durante a normalização: {str(e)}"],
                confidence_score=0.0
            )
        
        logger.info("=== FIM: Endpoint /validate - Sucesso ===")
        return response
        
    except Exception as e:
        logger.error(f"Erro inesperado ao processar validação: {e}")
        logger.error("=== FIM: Endpoint /validate - Erro ===")
        return ValidationResponse(
            success=False,
            normalized_data={},
            validation_errors=[f"Erro inesperado: {str(e)}"],
            confidence_score=0.0
        )


@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get session information and context"""
    logger.info(f"=== INÍCIO: Endpoint /sessions/{session_id} ===")
    
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        context = sessions[session_id]
        
        # Get session summary using ReasoningEngine
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
        
        logger.info(f"=== FIM: Endpoint /sessions/{session_id} - Sucesso ===")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter informações da sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    logger.info(f"=== INÍCIO: Endpoint DELETE /sessions/{session_id} ===")
    
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        del sessions[session_id]
        logger.info(f"Sessão removida: {session_id}")
        
        logger.info(f"=== FIM: Endpoint DELETE /sessions/{session_id} - Sucesso ===")
        return {"message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar sessão: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/sessions")
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


@app.get("/consultations")
async def list_consultations():
    """List all persisted consultations"""
    logger.info("=== INÍCIO: Endpoint /consultations ===")
    
    try:
        if consultation_service is None:
            raise HTTPException(status_code=503, detail="Consultation service não disponível")
        
        # Get consultations from service
        consultations = consultation_service.list_consultations(limit=50)
        
        logger.info(f"Listando {len(consultations)} consultas persistidas")
        logger.info("=== FIM: Endpoint /consultations - Sucesso ===")
        
        return {
            "consultations": consultations,
            "total_consultations": len(consultations),
            "timestamp": datetime.utcnow()
        }
        
    except HTTPException:
        logger.error("=== FIM: Endpoint /consultations - HTTPException ===")
        raise
    except Exception as e:
        logger.error(f"Erro ao listar consultas: {e}")
        logger.error("=== FIM: Endpoint /consultations - Erro ===")
        raise HTTPException(status_code=500, detail=f"Erro ao listar consultas: {str(e)}")


@app.get("/consultations/{consultation_id}")
async def get_consultation(consultation_id: int):
    """Get a specific consultation by ID"""
    logger.info(f"=== INÍCIO: Endpoint /consultations/{consultation_id} ===")
    
    try:
        if consultation_service is None:
            raise HTTPException(status_code=503, detail="Consultation service não disponível")
        
        # Get consultation from service
        consultation = consultation_service.get_consultation(consultation_id)
        
        if consultation is None:
            raise HTTPException(status_code=404, detail=f"Consulta com ID {consultation_id} não encontrada")
        
        logger.info(f"Consulta {consultation_id} recuperada com sucesso")
        logger.info("=== FIM: Endpoint /consultations/{consultation_id} - Sucesso ===")
        
        return consultation
        
    except HTTPException:
        logger.error("=== FIM: Endpoint /consultations/{consultation_id} - HTTPException ===")
        raise
    except Exception as e:
        logger.error(f"Erro ao recuperar consulta {consultation_id}: {e}")
        logger.error("=== FIM: Endpoint /consultations/{consultation_id} - Erro ===")
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar consulta: {str(e)}")