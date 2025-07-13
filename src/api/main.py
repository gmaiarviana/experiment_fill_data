from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.schemas.chat import ChatRequest, ChatResponse
from src.api.routers.system import router as system_router
from src.core.openai_client import OpenAIClient
from src.core.logging import setup_logging
from src.core.config import get_settings
from datetime import datetime
import uuid

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


@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint acessado")
    return {
        "message": "Data Structuring Agent API",
        "status": "running"
    }


@app.post("/chat/message")
async def chat_message(request: ChatRequest) -> ChatResponse:
    """Chat message endpoint"""
    logger.info(f"Chat message recebida: {request.message[:50]}...")
    
    try:
        if openai_client is None:
            logger.warning("OpenAI client não disponível")
            return ChatResponse(
                response="Desculpe, o serviço de IA não está disponível no momento. Tente novamente mais tarde.",
                session_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow()
            )
        
        # Get response from OpenAI
        ai_response = await openai_client.chat_completion(request.message)
        logger.info("Resposta do OpenAI gerada com sucesso")
        
        return ChatResponse(
            response=ai_response,
            session_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar chat message: {e}")
        return ChatResponse(
            response=f"Ocorreu um erro ao processar sua mensagem: {str(e)}",
            session_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow()
        ) 