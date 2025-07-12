from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.schemas.chat import ChatRequest, ChatResponse
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
    return ChatResponse(
        response="Olá! Como posso ajudar você hoje?",
        session_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow()
    ) 