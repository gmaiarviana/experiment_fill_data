from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ChatRequest(BaseModel):
    """Schema para requisições de chat"""
    message: str = Field(..., min_length=1, description="Mensagem do usuário")


class ChatResponse(BaseModel):
    """Schema para respostas de chat"""
    response: str = Field(..., description="Resposta do sistema")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da resposta")
    session_id: str = Field(..., description="ID da sessão do chat") 