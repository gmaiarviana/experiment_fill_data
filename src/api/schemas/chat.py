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
    session_id: Optional[str] = Field(None, description="ID da sessão (opcional, será gerado se não fornecido)")


class ChatResponse(BaseModel):
    """Schema para respostas de chat com dados do ReasoningEngine e persistência"""
    response: str = Field(..., description="Resposta do sistema")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da resposta")
    session_id: str = Field(..., description="ID da sessão do chat")
    action: Optional[str] = Field(None, description="Ação executada pelo ReasoningEngine")
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="Dados extraídos pela engine")
    confidence: Optional[float] = Field(None, description="Score de confiança da resposta (0.0-1.0)")
    next_questions: Optional[List[str]] = Field(None, description="Próximas perguntas sugeridas")
    consultation_id: Optional[int] = Field(None, description="ID da consulta persistida (se aplicável)")
    persistence_status: Optional[str] = Field(None, description="Status da persistência: success/failed/error/not_applicable")


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


class ValidationRequest(BaseModel):
    """Schema para requisições de validação de dados"""
    data: Dict[str, Any] = Field(..., description="Dados a serem validados e normalizados")
    domain: str = Field(default="consulta", description="Domínio dos dados (consulta, cadastro, etc.)")


class ValidationResponse(BaseModel):
    """Schema para respostas de validação de dados"""
    success: bool = Field(..., description="Indica se a validação foi bem-sucedida")
    normalized_data: Dict[str, Any] = Field(..., description="Dados normalizados")
    validation_errors: List[str] = Field(default_factory=list, description="Lista de erros de validação")
    confidence_score: float = Field(..., description="Score de confiança da validação (0.0-1.0)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da validação") 