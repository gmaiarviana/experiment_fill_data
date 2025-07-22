from fastapi import APIRouter, Request, HTTPException
from src.api.schemas.chat import EntityExtractionRequest, EntityExtractionResponse
from datetime import datetime
import json
import logging
from src.core.container import get_entity_extractor

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/extract/entities", response_model=EntityExtractionResponse)
async def extract_entities(request: Request) -> EntityExtractionResponse:
    """Entity extraction endpoint with detailed logging and validation"""
    logger.info("=== INÍCIO: Endpoint /extract/entities ===")
    try:
        logger.info(f"Content-Type: {request.headers.get('content-type', 'N/A')}")
        logger.info(f"Content-Length: {request.headers.get('content-length', 'N/A')}")
        body_bytes = await request.body()
        logger.info(f"Raw body length: {len(body_bytes)} bytes")
        try:
            body_text = body_bytes.decode('utf-8')
            logger.info(f"Body decoded as UTF-8: {body_text[:200]}...")
        except UnicodeDecodeError as e:
            logger.error(f"Erro de encoding UTF-8: {e}")
            raise HTTPException(status_code=400, detail="Invalid UTF-8 encoding in request body")
        try:
            body_json = json.loads(body_text)
            logger.info(f"JSON parsed successfully: {json.dumps(body_json, ensure_ascii=False)[:200]}...")
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao fazer parse do JSON: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        try:
            extraction_request = EntityExtractionRequest(**body_json)
            logger.info(f"EntityExtractionRequest validado com sucesso: message='{extraction_request.message[:50]}...'")
        except Exception as e:
            logger.error(f"Erro na validação Pydantic: {e}")
            raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
        entity_extractor = get_entity_extractor()
        if entity_extractor is None:
            logger.warning("Entity Extractor não disponível")
            return EntityExtractionResponse(
                success=False,
                error="Serviço de extração não está disponível no momento"
            )
        result = await entity_extractor.extract_consulta_entities(extraction_request.message)
        logger.info("Extração de entidades realizada com sucesso")
        logger.info(f"Result completo: {json.dumps(result, ensure_ascii=False, indent=2)}")
        if isinstance(result, dict) and result.get("success", False):
            response = EntityExtractionResponse(
                success=True,
                entities=result.get("extracted_data"),
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