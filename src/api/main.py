from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.schemas.chat import ChatRequest, ChatResponse
from src.core.openai_client import OpenAIClient
from datetime import datetime
import uuid


app = FastAPI(
    title="Data Structuring Agent",
    version="1.0.0"
)

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
except Exception as e:
    print(f"Erro ao inicializar OpenAI client: {e}")
    openai_client = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Data Structuring Agent API",
        "status": "running"
    }


@app.post("/chat/message")
async def chat_message(request: ChatRequest) -> ChatResponse:
    """Chat message endpoint"""
    try:
        if openai_client is None:
            return ChatResponse(
                response="Desculpe, o serviço de IA não está disponível no momento. Tente novamente mais tarde.",
                session_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow()
            )
        
        # Get response from OpenAI
        ai_response = await openai_client.chat_completion(request.message)
        
        return ChatResponse(
            response=ai_response,
            session_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        return ChatResponse(
            response=f"Ocorreu um erro ao processar sua mensagem: {str(e)}",
            session_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow()
        ) 