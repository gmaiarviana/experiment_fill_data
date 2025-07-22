from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging
from src.core.container import get_consultation_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/consultations")
async def list_consultations():
    """List all persisted consultations"""
    logger.info("=== INÍCIO: Endpoint /consultations ===")
    try:
        consultation_service = get_consultation_service()
        if consultation_service is None:
            raise HTTPException(status_code=503, detail="Consultation service não disponível")
        consultations = consultation_service.list_consultations(limit=50)
        logger.info(f"Listando {len(consultations)} consultas persistidas")
        logger.info("=== FIM: Endpoint /consultations - Sucesso ===")
        return {
            "consultations": consultations,
            "total_consultations": len(consultations),
            "timestamp": datetime.utcnow()
        }
    except HTTPException:
        logger.error("=== FIM: Endpoint /consultations - HTTPException ===")
        raise
    except Exception as e:
        logger.error(f"Erro ao listar consultas: {e}")
        logger.error("=== FIM: Endpoint /consultations - Erro ===")
        raise HTTPException(status_code=500, detail=f"Erro ao listar consultas: {str(e)}")

@router.get("/consultations/{consultation_id}")
async def get_consultation(consultation_id: int):
    """Get a specific consultation by ID"""
    logger.info(f"=== INÍCIO: Endpoint /consultations/{{consultation_id}} ===")
    try:
        consultation_service = get_consultation_service()
        if consultation_service is None:
            raise HTTPException(status_code=503, detail="Consultation service não disponível")
        consultation = consultation_service.get_consultation(consultation_id)
        if consultation is None:
            raise HTTPException(status_code=404, detail=f"Consulta com ID {consultation_id} não encontrada")
        logger.info(f"Consulta {consultation_id} recuperada com sucesso")
        logger.info("=== FIM: Endpoint /consultations/{consultation_id} - Sucesso ===")
        return consultation
    except HTTPException:
        logger.error("=== FIM: Endpoint /consultations/{consultation_id} - HTTPException ===")
        raise
    except Exception as e:
        logger.error(f"Erro ao recuperar consulta {consultation_id}: {e}")
        logger.error("=== FIM: Endpoint /consultations/{consultation_id} - Erro ===")
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar consulta: {str(e)}") 