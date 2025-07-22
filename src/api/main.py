from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.schemas.chat import ChatRequest, ChatResponse, EntityExtractionRequest, EntityExtractionResponse, ValidationRequest, ValidationResponse
from src.api.routers.system import router as system_router
from src.api.routers.chat import router as chat_router
from src.api.routers.extract import router as extract_router
# Imports moved to container for centralized management
from src.core.validation.normalizers.data_normalizer import DataNormalizer
from src.core.logging.logger_factory import get_logger
from src.core.config import get_settings
from src.core.database import create_tables
# ConsultationService imported via container
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
import json

# Get centralized settings
settings = get_settings()

# Setup logging with configured log level
logger = get_logger(__name__)

# Initialize unified data normalizer
data_normalizer = DataNormalizer()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

logger.info("✅ FastAPI app criada - main.py executando")

# Include routers
app.include_router(system_router)
app.include_router(chat_router)
app.include_router(extract_router)

# Configure CORS middleware with centralized settings
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services using ServiceContainer
from src.core.container import (
    ServiceContainer, 
    get_openai_client, 
    get_entity_extractor, 
    get_consultation_service
)
from src.core.reasoning.reasoning_coordinator import ReasoningCoordinator

# Initialize service container
try:
    service_container = ServiceContainer()
    service_container.initialize_services()
    logger.info("ServiceContainer inicializado com todos os servicos")
except Exception as e:
    logger.error(f"Erro ao inicializar ServiceContainer: {e}")
    service_container = None

# Global session management
sessions: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        logger.info("Creating database tables...")
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        # Don't fail startup - log and continue


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
        
        # Process validation using unified normalizer
        try:
            logger.info(f"Usando DataNormalizer unificado para domínio '{validation_request.domain}'")
            normalization_result = data_normalizer.normalize_consultation_data(validation_request.data)
            
            # Convert to expected format for backward compatibility  
            validation_errors = []
            for field_result in normalization_result.validation_summary.field_results.values():
                if field_result.errors:
                    validation_errors.extend(field_result.errors)
            
            result = {
                "normalized_data": normalization_result.normalized_data,
                "validation_errors": validation_errors,
                "confidence_score": normalization_result.confidence_score,
                "field_mapping_info": normalization_result.field_mapping_info,
                "success": normalization_result.success
            }
            
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
        
        # Get session summary using ReasoningCoordinator
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
        consultation_service = get_consultation_service()
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
        consultation_service = get_consultation_service()
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