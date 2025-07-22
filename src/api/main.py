from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.schemas.chat import ChatRequest, ChatResponse, EntityExtractionRequest, EntityExtractionResponse, ValidationRequest, ValidationResponse
from src.api.routers.system import router as system_router
from src.api.routers.chat import router as chat_router
from src.api.routers.extract import router as extract_router
from src.api.routers.validate import router as validate_router
from src.api.routers.sessions import router as sessions_router
from src.api.routers.consultations import router as consultations_router
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
app.include_router(consultations_router)

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


@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint acessado")
    return {
        "message": "Data Structuring Agent API",
        "status": "running"
    }