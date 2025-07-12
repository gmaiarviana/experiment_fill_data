from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Literal


class HealthResponse(BaseModel):
    """Schema para resposta de health check"""
    status: Literal["healthy", "unhealthy"] = Field(..., description="Status geral do sistema")
    services: Dict[str, Literal["healthy", "unhealthy"]] = Field(..., description="Status de cada serviço")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da verificação") 