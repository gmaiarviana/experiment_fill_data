from fastapi import APIRouter, Request
from src.api.schemas.chat import ValidationRequest, ValidationResponse
from src.core.validation.normalizers.data_normalizer import DataNormalizer
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
data_normalizer = DataNormalizer()

@router.post("/validate", response_model=ValidationResponse)
async def validate_data(request: Request) -> ValidationResponse:
    """Validation endpoint with detailed logging and error handling"""
    logger.info("=== INÍCIO: Endpoint /validate ===")
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
            return ValidationResponse(
                success=False,
                normalized_data={},
                validation_errors=[f"Invalid UTF-8 encoding in request body: {str(e)}"],
                confidence_score=0.0
            )
        try:
            body_json = json.loads(body_text)
            logger.info(f"JSON parsed successfully: {json.dumps(body_json, ensure_ascii=False)[:200]}...")
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao fazer parse do JSON: {e}")
            return ValidationResponse(
                success=False,
                normalized_data={},
                validation_errors=[f"Invalid JSON format: {str(e)}"],
                confidence_score=0.0
            )
        try:
            validation_request = ValidationRequest(**body_json)
            logger.info(f"ValidationRequest validado com sucesso: domain='{validation_request.domain}', data_keys={list(validation_request.data.keys()) if validation_request.data else None}")
        except Exception as e:
            logger.error(f"Erro na validação Pydantic: {e}")
            return ValidationResponse(
                success=False,
                normalized_data={},
                validation_errors=[f"Validation error: {str(e)}"],
                confidence_score=0.0
            )
        try:
            logger.info(f"Usando DataNormalizer unificado para domínio '{validation_request.domain}'")
            normalization_result = data_normalizer.normalize_consultation_data(validation_request.data)
            validation_errors = []
            for field_result in normalization_result.validation_summary.field_results.values():
                if field_result.errors:
                    validation_errors.extend(field_result.errors)
            result = {
                "normalized_data": normalization_result.normalized_data,
                "validation_errors": validation_errors,
                "confidence_score": normalization_result.confidence_score,
                "field_mapping_info": normalization_result.field_mapping_info,
                "success": normalization_result.success
            }
            logger.info("Validação realizada com sucesso")
            logger.info(f"Result completo: {json.dumps(result, ensure_ascii=False, indent=2)}")
            normalized_data = result.get("normalized_data", {}) if validation_request.domain == "consulta" else result.get("normalized_entities", {})
            validation_errors = result.get("validation_errors", [])
            confidence_score = result.get("confidence_score", 0.0)
            success = confidence_score > 0.0 and len(validation_errors) == 0
            response = ValidationResponse(
                success=success,
                normalized_data=normalized_data,
                validation_errors=validation_errors,
                confidence_score=confidence_score
            )
            logger.info(f"Response criada: success={response.success}, confidence={response.confidence_score}, errors_count={len(response.validation_errors)}")
        except Exception as e:
            logger.error(f"Erro durante a normalização: {e}")
            return ValidationResponse(
                success=False,
                normalized_data={},
                validation_errors=[f"Erro durante a normalização: {str(e)}"],
                confidence_score=0.0
            )
        logger.info("=== FIM: Endpoint /validate - Sucesso ===")
        return response
    except Exception as e:
        logger.error(f"Erro inesperado ao processar validação: {e}")
        logger.error("=== FIM: Endpoint /validate - Erro ===")
        return ValidationResponse(
            success=False,
            normalized_data={},
            validation_errors=[f"Erro inesperado: {str(e)}"],
            confidence_score=0.0
        ) 