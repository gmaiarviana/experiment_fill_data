"""
Validation Service for orchestrating data validation operations.

This service coordinates data validation including:
- Field-level validation
- Cross-field validation
- Business rule validation
- Validation result aggregation and reporting
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from src.core.validation.validation_orchestrator import ValidationOrchestrator
from src.core.validation.normalizers.data_normalizer import DataNormalizer
from src.core.validation.validators.base_validator import BaseValidator
from src.core.validation.validators.phone_validator import PhoneValidator
from src.core.validation.validators.date_validator import DateValidator
from src.core.validation.validators.name_validator import NameValidator
from src.core.validation.validators.document_validator import DocumentValidator

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Service for orchestrating data validation operations.
    
    Coordinates the complete validation flow including field validation,
    cross-field validation, business rules, and result aggregation.
    """
    
    def __init__(self):
        """Initialize ValidationService with required dependencies."""
        self.validation_orchestrator = ValidationOrchestrator()
        self.data_normalizer = DataNormalizer(strict_mode=False)
        
        # Initialize individual validators for specific use cases
        self.phone_validator = PhoneValidator()
        self.date_validator = DateValidator()
        self.name_validator = NameValidator()
        self.document_validator = DocumentValidator()
        
        logger.info("ValidationService initialized successfully")
    
    async def validate_consultation_data(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate consultation data comprehensively.
        
        Args:
            data: Data to validate
            context: Optional context for enhanced validation
            
        Returns:
            Dictionary containing validation results and recommendations
        """
        logger.info(f"Validating consultation data with {len(data)} fields")
        
        try:
            # Step 1: Normalize data first
            normalization_result = self.data_normalizer.normalize_consultation_data(data)
            normalized_data = normalization_result.normalized_data
            
            # Step 2: Perform comprehensive validation
            validation_result = await self._perform_comprehensive_validation(normalized_data, context)
            
            # Step 3: Apply business rules
            business_rules_result = self._apply_business_rules(normalized_data, validation_result, context)
            
            # Step 4: Generate recommendations
            recommendations = self._generate_validation_recommendations(validation_result, business_rules_result)
            
            # Step 5: Calculate overall validation score
            overall_score = self._calculate_validation_score(validation_result, business_rules_result)
            
            return {
                "success": True,
                "is_valid": overall_score >= 0.8,  # 80% threshold for validity
                "validation_score": overall_score,
                "normalized_data": normalized_data,
                "field_validations": validation_result.get("field_validations", {}),
                "business_rules": business_rules_result,
                "recommendations": recommendations,
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", []),
                "metadata": {
                    "validation_timestamp": datetime.utcnow().isoformat(),
                    "fields_validated": len(normalized_data),
                    "validation_rules_applied": len(validation_result.get("field_validations", {}))
                }
            }
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return self._create_validation_error_result(str(e))
    
    async def validate_single_field(self, field_name: str, field_value: Any, field_type: str = "auto") -> Dict[str, Any]:
        """
        Validate a single field with specific validation rules.
        
        Args:
            field_name: Name of the field to validate
            field_value: Value to validate
            field_type: Type of field for validation (auto, phone, date, name, document)
            
        Returns:
            Dictionary containing field validation result
        """
        logger.info(f"Validating field '{field_name}' with value '{field_value}'")
        
        try:
            # Auto-detect field type if not specified
            if field_type == "auto":
                field_type = self._detect_field_type(field_name, field_value)
            
            # Get appropriate validator
            validator = self._get_validator_for_field_type(field_type)
            
            if validator:
                validation_result = validator.validate(field_value)
                return {
                    "success": True,
                    "field_name": field_name,
                    "field_value": field_value,
                    "field_type": field_type,
                    "is_valid": validation_result.is_valid,
                    "normalized_value": validation_result.value,
                    "error_message": validation_result.errors[0] if validation_result.errors else None,
                    "confidence": validation_result.confidence
                }
            else:
                return {
                    "success": False,
                    "field_name": field_name,
                    "field_value": field_value,
                    "field_type": field_type,
                    "error": f"No validator found for field type: {field_type}"
                }
                
        except Exception as e:
            logger.error(f"Error validating field '{field_name}': {e}")
            return {
                "success": False,
                "field_name": field_name,
                "field_value": field_value,
                "error": str(e)
            }
    
    async def validate_batch(self, data_batch: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Validate multiple data records in batch.
        
        Args:
            data_batch: List of data records to validate
            context: Optional context for enhanced validation
            
        Returns:
            List of validation results for each record
        """
        logger.info(f"Processing batch validation for {len(data_batch)} records")
        
        results = []
        for i, data in enumerate(data_batch):
            try:
                result = await self.validate_consultation_data(data, context)
                result["record_index"] = i
                results.append(result)
            except Exception as e:
                logger.error(f"Error validating record {i}: {e}")
                results.append(self._create_validation_error_result(str(e), record_index=i))
        
        return results
    
    async def _perform_comprehensive_validation(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform comprehensive validation on all fields."""
        field_validations = {}
        errors = []
        warnings = []
        
        # Validate each field
        for field_name, field_value in data.items():
            if field_value is not None and field_value != "":
                field_type = self._detect_field_type(field_name, field_value)
                validator = self._get_validator_for_field_type(field_type)
                
                if validator:
                    validation_result = validator.validate(field_value)
                    field_validations[field_name] = {
                        "is_valid": validation_result.is_valid,
                        "normalized_value": validation_result.value,
                        "error_message": validation_result.errors[0] if validation_result.errors else None,
                        "confidence": validation_result.confidence,
                        "field_type": field_type
                    }
                    
                    if not validation_result.is_valid:
                        error_msg = validation_result.errors[0] if validation_result.errors else "Validation failed"
                        errors.append(f"{field_name}: {error_msg}")
                    elif validation_result.confidence < 0.8:
                        warnings.append(f"{field_name}: Low confidence ({validation_result.confidence:.2f})")
        
        return {
            "field_validations": field_validations,
            "errors": errors,
            "warnings": warnings
        }
    
    def _apply_business_rules(self, data: Dict[str, Any], validation_result: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply business rules and cross-field validations."""
        business_rules = {
            "rules_applied": [],
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Rule 1: Required fields for consultation
        required_fields = ["nome", "telefone"]
        missing_required = [field for field in required_fields if not data.get(field)]
        if missing_required:
            business_rules["violations"].append(f"Missing required fields: {', '.join(missing_required)}")
            business_rules["recommendations"].append("Please provide name and phone number")
        
        # Rule 2: Date validation (must be future)
        if data.get("data"):
            try:
                from datetime import datetime
                consultation_date = datetime.strptime(data["data"], "%Y-%m-%d")
                if consultation_date <= datetime.now():
                    business_rules["violations"].append("Consultation date must be in the future")
                    business_rules["recommendations"].append("Please select a future date")
            except ValueError:
                business_rules["violations"].append("Invalid date format")
        
        # Rule 3: Time validation (business hours)
        if data.get("horario"):
            try:
                hour = int(data["horario"].split(":")[0])
                if hour < 8 or hour > 18:
                    business_rules["warnings"].append("Consultation time is outside business hours (8:00-18:00)")
            except (ValueError, IndexError):
                business_rules["violations"].append("Invalid time format")
        
        # Rule 4: Phone number format consistency
        if data.get("telefone"):
            phone_validation = validation_result.get("field_validations", {}).get("telefone", {})
            if phone_validation.get("is_valid", False) and phone_validation.get("confidence", 0) < 0.9:
                business_rules["warnings"].append("Phone number format may need verification")
        
        business_rules["rules_applied"] = [
            "required_fields_check",
            "future_date_validation", 
            "business_hours_check",
            "phone_format_consistency"
        ]
        
        return business_rules
    
    def _generate_validation_recommendations(self, validation_result: Dict[str, Any], business_rules: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []
        
        # Add business rule recommendations
        recommendations.extend(business_rules.get("recommendations", []))
        
        # Add field-specific recommendations
        field_validations = validation_result.get("field_validations", {})
        for field_name, validation in field_validations.items():
            if not validation.get("is_valid", True):
                recommendations.append(f"Please check the {field_name} field")
            elif validation.get("confidence", 1.0) < 0.8:
                recommendations.append(f"Please verify the {field_name} information")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _calculate_validation_score(self, validation_result: Dict[str, Any], business_rules: Dict[str, Any]) -> float:
        """Calculate overall validation score (0.0 to 1.0)."""
        field_validations = validation_result.get("field_validations", {})
        
        if not field_validations:
            return 0.0
        
        # Calculate field-level score
        total_fields = len(field_validations)
        valid_fields = sum(1 for v in field_validations.values() if v.get("is_valid", False))
        field_score = valid_fields / total_fields if total_fields > 0 else 0.0
        
        # Calculate confidence score
        confidence_scores = [v.get("confidence", 0.0) for v in field_validations.values()]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Calculate business rules score
        violations = len(business_rules.get("violations", []))
        warnings = len(business_rules.get("warnings", []))
        business_score = max(0.0, 1.0 - (violations * 0.3 + warnings * 0.1))
        
        # Weighted combination
        final_score = (field_score * 0.4 + avg_confidence * 0.4 + business_score * 0.2)
        
        return max(0.0, min(1.0, final_score))
    
    def _detect_field_type(self, field_name: str, field_value: Any) -> str:
        """Auto-detect field type based on field name and value."""
        field_name_lower = field_name.lower()
        
        if "telefone" in field_name_lower or "phone" in field_name_lower:
            return "phone"
        elif "data" in field_name_lower or "date" in field_name_lower:
            return "date"
        elif "nome" in field_name_lower or "name" in field_name_lower:
            return "name"
        elif "cpf" in field_name_lower or "document" in field_name_lower:
            return "document"
        elif "horario" in field_name_lower or "time" in field_name_lower:
            return "time"
        else:
            return "text"
    
    def _get_validator_for_field_type(self, field_type: str) -> Optional[BaseValidator]:
        """Get appropriate validator for field type."""
        validators = {
            "phone": self.phone_validator,
            "date": self.date_validator,
            "name": self.name_validator,
            "document": self.document_validator
        }
        return validators.get(field_type)
    
    def _create_validation_error_result(self, error_message: str, record_index: Optional[int] = None) -> Dict[str, Any]:
        """Create standardized error result for validation failures."""
        result = {
            "success": False,
            "error": error_message,
            "is_valid": False,
            "validation_score": 0.0,
            "normalized_data": {},
            "field_validations": {},
            "business_rules": {
                "rules_applied": [],
                "violations": [error_message],
                "recommendations": []
            },
            "recommendations": ["Please check the data and try again"],
            "errors": [error_message],
            "warnings": [],
            "metadata": {
                "validation_timestamp": datetime.utcnow().isoformat(),
                "error_type": "validation_failure"
            }
        }
        
        if record_index is not None:
            result["record_index"] = record_index
        
        return result
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get available validation rules and their descriptions."""
        return {
            "field_types": {
                "phone": "Brazilian phone number validation",
                "date": "Date validation with future date check",
                "name": "Name validation and normalization",
                "document": "CPF and document validation",
                "time": "Time format validation"
            },
            "business_rules": [
                "Required fields: name and phone",
                "Future date validation",
                "Business hours check (8:00-18:00)",
                "Phone format consistency"
            ]
        } 