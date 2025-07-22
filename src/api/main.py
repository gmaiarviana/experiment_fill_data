from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.schemas.chat import ChatRequest, ChatResponse, EntityExtractionRequest, EntityExtractionResponse, ValidationRequest, ValidationResponse
from src.api.routers.system import router as system_router
from src.api.routers.chat import router as chat_router
from src.api.routers.extract import router as extract_router
from src.api.routers.validate import router as validate_router
from src.api.routers.sessions import router as sessions_router
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
app.include_router(validate_router)
app.include_router(sessions_router)

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