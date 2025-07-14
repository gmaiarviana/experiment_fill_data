from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List


class ChatRequest(BaseModel):
    """Schema para requisições de chat"""
    message: str = Field(
        ..., 
        min_length=1, 
        max_length=1000, 
        description="Mensagem não pode ser vazia",
        example="Olá, preciso de ajuda"
    )


class ChatResponse(BaseModel):
    """Schema para respostas de chat"""
    response: str = Field(..., description="Resposta do sistema")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da resposta")
    session_id: str = Field(..., description="ID da sessão do chat")


class EntityExtractionRequest(BaseModel):
    """Schema específico para requisições de extração de entidades"""
    message: str = Field(
        ..., 
        min_length=1, 
        max_length=2000, 
        description="Texto para extração de entidades",
        example="Preciso de um relatório de vendas do mês passado"
    )


class EntityExtractionResponse(BaseModel):
    """Schema para respostas de extração de entidades"""
    success: bool = Field(..., description="Indica se a extração foi bem-sucedida")
    entities: Optional[Dict[str, Any]] = Field(None, description="Entidades extraídas (extracted_data)")
    confidence_score: Optional[float] = Field(None, description="Score de confiança da extração (0.0-1.0)")
    missing_fields: Optional[list] = Field(None, description="Campos que não foram preenchidos")
    suggested_questions: Optional[list] = Field(None, description="Perguntas sugeridas para campos faltantes")
    is_complete: Optional[bool] = Field(None, description="Indica se todos os campos foram preenchidos")
    error: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da extração") 