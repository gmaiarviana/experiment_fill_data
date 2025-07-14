from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.schemas.chat import ChatRequest, ChatResponse, EntityExtractionRequest, EntityExtractionResponse
from src.api.routers.system import router as system_router
from src.core.openai_client import OpenAIClient
from src.core.entity_extraction import EntityExtractor
from src.core.logging import setup_logging
from src.core.config import get_settings
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
    """Chat message endpoint with detailed logging and validation"""
    logger.info("=== INÍCIO: Endpoint /chat/message ===")
    
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
        
        # Process chat message
        if openai_client is None:
            logger.warning("OpenAI client não disponível")
            return ChatResponse(
                response="Desculpe, o serviço de IA não está disponível no momento. Tente novamente mais tarde.",
                session_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow()
            )
        
        # Get response from OpenAI
        ai_response = await openai_client.chat_completion(chat_request.message)
        logger.info("Resposta do OpenAI gerada com sucesso")
        
        response = ChatResponse(
            response=ai_response,
            session_id=str(uuid.uuid4()),
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