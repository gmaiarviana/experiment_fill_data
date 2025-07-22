from fastapi import APIRouter, HTTPException
import asyncio
from datetime import datetime
from typing import Dict, Literal

from src.api.schemas.system import HealthResponse
from src.core.config import get_settings


router = APIRouter(prefix="/system", tags=["system"])


async def check_postgres_connection() -> Literal["healthy", "unhealthy"]:
    """Verifica conexão com PostgreSQL"""
    try:
        settings = get_settings()
        
        # Import asyncpg apenas se necessário
        import asyncpg
        
        # Extrair parâmetros da URL
        # Formato esperado: postgresql://user:password@host:port/database
        conn = await asyncio.wait_for(
            asyncpg.connect(settings.DATABASE_URL),
            timeout=settings.DB_CONNECTION_TIMEOUT
        )
        await conn.close()
        return "healthy"
        
    except Exception as e:
        print(f"Erro na conexão PostgreSQL: {e}")
        return "unhealthy"


async def check_fastapi_status() -> Literal["healthy", "unhealthy"]:
    """Verifica status do FastAPI (sempre healthy se endpoint responder)"""
    try:
        # Se chegou até aqui, o FastAPI está funcionando
        return "healthy"
    except Exception:
        return "unhealthy"


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint para verificar status dos serviços"""
    try:
        # Verificar serviços em paralelo
        postgres_status, fastapi_status = await asyncio.gather(
            check_postgres_connection(),
            check_fastapi_status(),
            return_exceptions=True
        )
        
        # Tratar exceções dos serviços
        if isinstance(postgres_status, Exception):
            postgres_status = "unhealthy"
        if isinstance(fastapi_status, Exception):
            fastapi_status = "unhealthy"
        
        services = {
            "postgres": postgres_status,
            "fastapi": fastapi_status
        }
        
        # Status geral é unhealthy se qualquer serviço estiver unhealthy
        overall_status = "healthy" if all(status == "healthy" for status in services.values()) else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            services=services,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        # Em caso de erro geral, retornar unhealthy
        return HealthResponse(
            status="unhealthy",
            services={
                "postgres": "unhealthy",
                "fastapi": "unhealthy"
            },
            timestamp=datetime.utcnow()
        ) 