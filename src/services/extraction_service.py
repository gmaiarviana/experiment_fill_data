"""
Extraction Service for managing entity extraction operations.

This service coordinates entity extraction including:
- Message preprocessing and enhancement
- Entity extraction with context awareness
- Data normalization and validation
- Confidence scoring and quality assessment
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from src.core.entity_extraction import EntityExtractor
from src.core.validation.normalizers.data_normalizer import DataNormalizer
from src.core.validation.validation_orchestrator import ValidationOrchestrator
from src.core.container import get_entity_extractor

logger = logging.getLogger(__name__)


class ExtractionService:
    """
    Service for managing entity extraction operations.
    
    Coordinates the complete extraction flow including preprocessing,
    entity extraction, validation, and quality assessment.
    """
    
    def __init__(self, entity_extractor: Optional[EntityExtractor] = None):
        """
        Initialize ExtractionService with required dependencies.
        
        Args:
            entity_extractor: EntityExtractor instance for dependency injection
        """
        self.entity_extractor = entity_extractor or get_entity_extractor()
        self.data_normalizer = DataNormalizer(strict_mode=False)
        self.validation_orchestrator = ValidationOrchestrator()
        logger.info("ExtractionService initialized successfully")
    
    async def extract_entities(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract entities from a natural language message.
        
        Args:
            message: Natural language message to extract entities from
            context: Optional session context for enhanced extraction
            
        Returns:
            Dictionary containing extraction results with metadata
        """
        logger.info(f"Extracting entities from message: {message[:50]}...")
        
        try:
            # Preprocess message with context
            enhanced_message = self._enhance_message_with_context(message, context)
            
            # Extract entities using EntityExtractor
            extraction_result = await self.entity_extractor.extract_consulta_entities(
                enhanced_message, context
            )
            
            if not extraction_result.get("success", False):
                return self._create_extraction_error_result(
                    extraction_result.get("error", "Unknown extraction error")
                )
            
            # Get extracted data
            extracted_data = extraction_result.get("extracted_data", {})
            confidence_score = extraction_result.get("confidence_score", 0.0)
            
            # Validate and normalize extracted data
            validation_result = await self._validate_and_normalize_data(extracted_data, context)
            
            # Calculate final confidence score
            final_confidence = self._calculate_final_confidence(
                confidence_score, validation_result, context
            )
            
            # Prepare final result
            result = {
                "success": True,
                "extracted_data": validation_result.get("normalized_data", extracted_data),
                "raw_data": extracted_data,
                "confidence_score": final_confidence,
                "validation_summary": validation_result.get("validation_summary", {}),
                "quality_metrics": self._calculate_quality_metrics(extracted_data, validation_result),
                "metadata": {
                    "extraction_timestamp": datetime.utcnow().isoformat(),
                    "message_length": len(message),
                    "entities_found": len([v for v in extracted_data.values() if v is not None]),
                    "context_used": context is not None
                }
            }
            
            logger.info(f"Entity extraction completed successfully. Confidence: {final_confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error during entity extraction: {e}")
            return self._create_extraction_error_result(str(e))
    
    async def extract_entities_batch(self, messages: List[str], context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extract entities from multiple messages in batch.
        
        Args:
            messages: List of natural language messages
            context: Optional session context for enhanced extraction
            
        Returns:
            List of extraction results for each message
        """
        logger.info(f"Processing batch extraction for {len(messages)} messages")
        
        results = []
        for i, message in enumerate(messages):
            try:
                result = await self.extract_entities(message, context)
                result["message_index"] = i
                results.append(result)
            except Exception as e:
                logger.error(f"Error extracting entities from message {i}: {e}")
                results.append(self._create_extraction_error_result(str(e), message_index=i))
        
        return results
    
    def _enhance_message_with_context(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Enhance message with context information for better extraction."""
        if not context:
            return message
        
        # Get existing extracted data from context
        existing_data = context.get("extracted_data", {})
        
        # Build context enhancement
        context_parts = []
        
        if existing_data.get("nome"):
            context_parts.append(f"Paciente: {existing_data['nome']}")
        
        if existing_data.get("telefone"):
            context_parts.append(f"Telefone: {existing_data['telefone']}")
        
        if existing_data.get("data"):
            context_parts.append(f"Data anterior: {existing_data['data']}")
        
        if existing_data.get("horario"):
            context_parts.append(f"Horário anterior: {existing_data['horario']}")
        
        if existing_data.get("tipo_consulta"):
            context_parts.append(f"Tipo de consulta: {existing_data['tipo_consulta']}")
        
        # Enhance message with context
        if context_parts:
            enhanced_message = f"Contexto: {' | '.join(context_parts)}\n\nMensagem: {message}"
            logger.debug(f"Enhanced message with context: {enhanced_message[:100]}...")
            return enhanced_message
        
        return message
    
    async def _validate_and_normalize_data(self, extracted_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate and normalize extracted data."""
        try:
            # Use existing data normalizer for consistency
            normalization_result = self.data_normalizer.normalize_consultation_data(extracted_data)
            
            # Additional validation if needed
            validation_errors = []
            if normalization_result.validation_summary.field_results:
                for field, result in normalization_result.validation_summary.field_results.items():
                    if not result.is_valid:
                        validation_errors.append(f"{field}: {result.error_message}")
            
            return {
                "normalized_data": normalization_result.normalized_data,
                "validation_summary": {
                    "is_valid": len(validation_errors) == 0,
                    "errors": validation_errors,
                    "field_results": normalization_result.validation_summary.field_results
                }
            }
            
        except Exception as e:
            logger.error(f"Error during validation and normalization: {e}")
            return {
                "normalized_data": extracted_data,
                "validation_summary": {
                    "is_valid": False,
                    "errors": [f"Validation error: {str(e)}"],
                    "field_results": {}
                }
            }
    
    def _calculate_final_confidence(self, extraction_confidence: float, validation_result: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> float:
        """Calculate final confidence score based on extraction and validation."""
        base_confidence = extraction_confidence
        
        # Adjust based on validation results
        validation_summary = validation_result.get("validation_summary", {})
        if validation_summary.get("is_valid", False):
            base_confidence *= 1.1  # Boost confidence for valid data
        else:
            base_confidence *= 0.8  # Reduce confidence for validation errors
        
        # Adjust based on context completeness
        if context:
            existing_data = context.get("extracted_data", {})
            existing_fields = len([v for v in existing_data.values() if v is not None])
            if existing_fields > 0:
                base_confidence *= 1.05  # Slight boost for context-aware extraction
        
        # Ensure confidence is within bounds
        return max(0.0, min(1.0, base_confidence))
    
    def _calculate_quality_metrics(self, extracted_data: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quality metrics for extracted data."""
        total_fields = len(extracted_data)
        filled_fields = len([v for v in extracted_data.values() if v is not None and v != ""])
        
        validation_summary = validation_result.get("validation_summary", {})
        valid_fields = 0
        if validation_summary.get("field_results"):
            valid_fields = len([
                result for result in validation_summary["field_results"].values() 
                if result.is_valid
            ])
        
        return {
            "completeness": filled_fields / total_fields if total_fields > 0 else 0.0,
            "validity": valid_fields / total_fields if total_fields > 0 else 0.0,
            "total_fields": total_fields,
            "filled_fields": filled_fields,
            "valid_fields": valid_fields,
            "validation_errors": len(validation_summary.get("errors", []))
        }
    
    def _create_extraction_error_result(self, error_message: str, message_index: Optional[int] = None) -> Dict[str, Any]:
        """Create standardized error result for extraction failures."""
        result = {
            "success": False,
            "error": error_message,
            "extracted_data": {},
            "raw_data": {},
            "confidence_score": 0.0,
            "validation_summary": {
                "is_valid": False,
                "errors": [error_message],
                "field_results": {}
            },
            "quality_metrics": {
                "completeness": 0.0,
                "validity": 0.0,
                "total_fields": 0,
                "filled_fields": 0,
                "valid_fields": 0,
                "validation_errors": 1
            },
            "metadata": {
                "extraction_timestamp": datetime.utcnow().isoformat(),
                "error_type": "extraction_failure"
            }
        }
        
        if message_index is not None:
            result["message_index"] = message_index
        
        return result
    
    def get_extraction_schema(self) -> Dict[str, Any]:
        """Get the extraction schema for reference."""
        if self.entity_extractor:
            return self.entity_extractor.get_schema()
        return {}
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types."""
        schema = self.get_extraction_schema()
        if schema and "parameters" in schema and "properties" in schema["parameters"]:
            return list(schema["parameters"]["properties"].keys())
        return [] 