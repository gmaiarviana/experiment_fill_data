import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from src.services.validation_service import ValidationService
from src.core.validation.normalizers.data_normalizer import NormalizationResult, ValidationSummary
from src.core.validation.validators.base_validator import ValidationResult


class TestValidationService:
    """Testes para o serviço de validação."""

    def setup_method(self):
        """Setup para cada teste."""
        self.validation_service = ValidationService()

    def test_validation_service_initialization(self):
        """Testa inicialização do ValidationService."""
        assert self.validation_service.validation_orchestrator is not None
        assert self.validation_service.data_normalizer is not None
        assert self.validation_service.phone_validator is not None
        assert self.validation_service.date_validator is not None
        assert self.validation_service.name_validator is not None
        assert self.validation_service.document_validator is not None

    @patch.object(ValidationService, '_perform_comprehensive_validation')
    @patch.object(ValidationService, '_apply_business_rules')
    @patch.object(ValidationService, '_generate_validation_recommendations')
    @pytest.mark.asyncio
    async def test_validate_consultation_data_success(self, mock_recommendations, mock_business_rules, mock_validation):
        """Testa validação de dados de consulta bem-sucedida."""
        # Setup mock normalization result
        mock_validation_summary = MagicMock(spec=ValidationSummary)
        mock_normalization_result = MagicMock(spec=NormalizationResult)
        mock_normalization_result.normalized_data = {
            "nome": "João Silva",
            "telefone": "(11) 99988-8777",
            "data": "2025-07-25",
            "horario": "14:00"
        }
        mock_normalization_result.validation_summary = mock_validation_summary
        
        self.validation_service.data_normalizer.normalize_consultation_data.return_value = mock_normalization_result
        
        # Setup mock validation result
        mock_validation.return_value = {
            "field_validations": {
                "nome": {"is_valid": True, "confidence": 0.95},
                "telefone": {"is_valid": True, "confidence": 0.9},
                "data": {"is_valid": True, "confidence": 1.0},
                "horario": {"is_valid": True, "confidence": 0.9}
            },
            "errors": [],
            "warnings": []
        }
        
        mock_business_rules.return_value = {
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        mock_recommendations.return_value = []

        data = {
            "nome": "joão silva",
            "telefone": "11999888777",
            "data": "25/07/2025",
            "horario": "14:00"
        }

        result = await self.validation_service.validate_consultation_data(data)

        assert result["success"] is True
        assert result["is_valid"] is True
        assert result["validation_score"] > 0.8
        assert "normalized_data" in result
        assert "field_validations" in result

    @pytest.mark.asyncio
    async def test_validate_consultation_data_with_errors(self):
        """Testa validação com dados inválidos."""
        # Mock normalization with errors
        mock_validation_summary = MagicMock(spec=ValidationSummary)
        mock_normalization_result = MagicMock(spec=NormalizationResult)
        mock_normalization_result.normalized_data = {
            "nome": "j",  # Nome muito curto
            "telefone": "123",  # Telefone inválido
            "data": "ontem",  # Data inválida
        }
        
        self.validation_service.data_normalizer.normalize_consultation_data.return_value = mock_normalization_result
        
        # Mock validator responses
        invalid_result = MagicMock(spec=ValidationResult)
        invalid_result.is_valid = False
        invalid_result.value = None
        invalid_result.errors = ["Invalid value"]
        invalid_result.confidence = 0.0
        
        self.validation_service.name_validator.validate.return_value = invalid_result
        self.validation_service.phone_validator.validate.return_value = invalid_result
        self.validation_service.date_validator.validate.return_value = invalid_result

        data = {
            "nome": "j",
            "telefone": "123",
            "data": "ontem"
        }

        result = await self.validation_service.validate_consultation_data(data)

        assert result["success"] is True  # Service should not fail
        assert result["is_valid"] is False  # But data should be invalid
        assert result["validation_score"] < 0.8
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_validate_single_field_phone(self):
        """Testa validação de campo único - telefone."""
        valid_result = MagicMock(spec=ValidationResult)
        valid_result.is_valid = True
        valid_result.value = "(11) 99988-8777"
        valid_result.errors = []
        valid_result.confidence = 0.95
        
        self.validation_service.phone_validator.validate.return_value = valid_result

        result = await self.validation_service.validate_single_field("telefone", "11999888777", "phone")

        assert result["success"] is True
        assert result["is_valid"] is True
        assert result["normalized_value"] == "(11) 99988-8777"
        assert result["field_type"] == "phone"
        assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_validate_single_field_auto_detect(self):
        """Testa validação com auto-detecção do tipo de campo."""
        valid_result = MagicMock(spec=ValidationResult)
        valid_result.is_valid = True
        valid_result.value = "João Silva"
        valid_result.errors = []
        valid_result.confidence = 0.9
        
        self.validation_service.name_validator.validate.return_value = valid_result

        result = await self.validation_service.validate_single_field("nome", "joão silva", "auto")

        assert result["success"] is True
        assert result["field_type"] == "name"
        assert result["normalized_value"] == "João Silva"

    @pytest.mark.asyncio
    async def test_validate_single_field_invalid(self):
        """Testa validação de campo inválido."""
        invalid_result = MagicMock(spec=ValidationResult)
        invalid_result.is_valid = False
        invalid_result.value = None
        invalid_result.errors = ["Invalid phone number"]
        invalid_result.confidence = 0.0
        
        self.validation_service.phone_validator.validate.return_value = invalid_result

        result = await self.validation_service.validate_single_field("telefone", "123", "phone")

        assert result["success"] is True
        assert result["is_valid"] is False
        assert result["error_message"] == "Invalid phone number"
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_validate_batch_success(self):
        """Testa validação em lote bem-sucedida."""
        # Mock successful validation for all records
        mock_validation_summary = MagicMock(spec=ValidationSummary)
        mock_normalization_result = MagicMock(spec=NormalizationResult)
        mock_normalization_result.normalized_data = {"nome": "João Silva"}
        mock_normalization_result.validation_summary = mock_validation_summary
        
        self.validation_service.data_normalizer.normalize_consultation_data.return_value = mock_normalization_result
        
        # Mock validator
        valid_result = MagicMock(spec=ValidationResult)
        valid_result.is_valid = True
        valid_result.value = "João Silva"
        valid_result.errors = []
        valid_result.confidence = 0.9
        
        self.validation_service.name_validator.validate.return_value = valid_result

        data_batch = [
            {"nome": "João Silva", "telefone": "11999888777"},
            {"nome": "Maria Santos", "telefone": "11888777666"}
        ]

        results = await self.validation_service.validate_batch(data_batch)

        assert len(results) == 2
        assert results[0]["record_index"] == 0
        assert results[1]["record_index"] == 1
        assert all(result["success"] for result in results)

    def test_detect_field_type(self):
        """Testa detecção automática do tipo de campo."""
        assert self.validation_service._detect_field_type("telefone", "11999888777") == "phone"
        assert self.validation_service._detect_field_type("data", "2025-07-25") == "date"
        assert self.validation_service._detect_field_type("nome", "João Silva") == "name"
        assert self.validation_service._detect_field_type("cpf", "12345678901") == "document"
        assert self.validation_service._detect_field_type("horario", "14:00") == "time"
        assert self.validation_service._detect_field_type("observacoes", "texto qualquer") == "text"

    def test_get_validator_for_field_type(self):
        """Testa obtenção de validador para tipo de campo."""
        assert self.validation_service._get_validator_for_field_type("phone") == self.validation_service.phone_validator
        assert self.validation_service._get_validator_for_field_type("date") == self.validation_service.date_validator
        assert self.validation_service._get_validator_for_field_type("name") == self.validation_service.name_validator
        assert self.validation_service._get_validator_for_field_type("document") == self.validation_service.document_validator
        assert self.validation_service._get_validator_for_field_type("unknown") is None

    def test_apply_business_rules_missing_required_fields(self):
        """Testa aplicação de regras de negócio para campos obrigatórios."""
        data = {
            "data": "2025-07-25",
            "horario": "14:00"
        }
        
        validation_result = {"field_validations": {}}
        
        business_rules = self.validation_service._apply_business_rules(data, validation_result)

        assert len(business_rules["violations"]) > 0
        assert any("Missing required fields" in violation for violation in business_rules["violations"])
        assert any("name and phone" in rec for rec in business_rules["recommendations"])

    def test_apply_business_rules_past_date(self):
        """Testa regra de negócio para data no passado."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        data = {
            "nome": "João Silva",
            "telefone": "11999888777",
            "data": yesterday,
            "horario": "14:00"
        }
        
        validation_result = {"field_validations": {}}
        
        business_rules = self.validation_service._apply_business_rules(data, validation_result)

        assert any("future" in violation.lower() for violation in business_rules["violations"])

    def test_apply_business_rules_outside_business_hours(self):
        """Testa regra de negócio para horário fora do expediente."""
        data = {
            "nome": "João Silva",
            "telefone": "11999888777",
            "data": "2025-07-25",
            "horario": "20:00"  # Após 18h
        }
        
        validation_result = {"field_validations": {}}
        
        business_rules = self.validation_service._apply_business_rules(data, validation_result)

        assert any("business hours" in warning for warning in business_rules["warnings"])

    def test_calculate_validation_score_high_score(self):
        """Testa cálculo de score de validação alto."""
        validation_result = {
            "field_validations": {
                "nome": {"is_valid": True, "confidence": 0.95},
                "telefone": {"is_valid": True, "confidence": 0.9},
                "data": {"is_valid": True, "confidence": 1.0}
            }
        }
        
        business_rules = {
            "violations": [],
            "warnings": []
        }

        score = self.validation_service._calculate_validation_score(validation_result, business_rules)

        assert score >= 0.8
        assert score <= 1.0

    def test_calculate_validation_score_low_score(self):
        """Testa cálculo de score de validação baixo."""
        validation_result = {
            "field_validations": {
                "nome": {"is_valid": False, "confidence": 0.2},
                "telefone": {"is_valid": False, "confidence": 0.1},
                "data": {"is_valid": True, "confidence": 0.8}
            }
        }
        
        business_rules = {
            "violations": ["Missing required fields", "Invalid phone"],
            "warnings": ["Low confidence"]
        }

        score = self.validation_service._calculate_validation_score(validation_result, business_rules)

        assert score < 0.5

    def test_generate_validation_recommendations(self):
        """Testa geração de recomendações de validação."""
        validation_result = {
            "field_validations": {
                "nome": {"is_valid": False, "confidence": 0.2},
                "telefone": {"is_valid": True, "confidence": 0.7}  # Low confidence
            }
        }
        
        business_rules = {
            "recommendations": ["Please provide required information"]
        }

        recommendations = self.validation_service._generate_validation_recommendations(validation_result, business_rules)

        assert "Please provide required information" in recommendations
        assert any("nome" in rec for rec in recommendations)
        assert any("telefone" in rec for rec in recommendations)

    def test_create_validation_error_result(self):
        """Testa criação de resultado de erro de validação."""
        error_message = "Validation failed"
        
        result = self.validation_service._create_validation_error_result(error_message)

        assert result["success"] is False
        assert result["error"] == error_message
        assert result["is_valid"] is False
        assert result["validation_score"] == 0.0
        assert error_message in result["errors"]
        assert "validation_failure" in result["metadata"]["error_type"]

    def test_create_validation_error_result_with_record_index(self):
        """Testa criação de resultado de erro com índice do registro."""
        result = self.validation_service._create_validation_error_result("Error", record_index=2)

        assert result["record_index"] == 2

    def test_get_validation_rules(self):
        """Testa obtenção das regras de validação."""
        rules = self.validation_service.get_validation_rules()

        assert "field_types" in rules
        assert "business_rules" in rules
        assert "phone" in rules["field_types"]
        assert "date" in rules["field_types"]
        assert len(rules["business_rules"]) > 0


class TestValidationServiceErrorHandling:
    """Testes para tratamento de erros no ValidationService."""

    def setup_method(self):
        """Setup para cada teste."""
        self.validation_service = ValidationService()

    @pytest.mark.asyncio
    async def test_validate_consultation_data_exception(self):
        """Testa tratamento de exceção geral na validação."""
        self.validation_service.data_normalizer.normalize_consultation_data.side_effect = Exception("Normalization error")

        result = await self.validation_service.validate_consultation_data({"nome": "João"})

        assert result["success"] is False
        assert "Normalization error" in result["error"]
        assert result["validation_score"] == 0.0

    @pytest.mark.asyncio
    async def test_validate_single_field_exception(self):
        """Testa tratamento de exceção na validação de campo único."""
        self.validation_service.name_validator.validate.side_effect = Exception("Validator error")

        result = await self.validation_service.validate_single_field("nome", "João", "name")

        assert result["success"] is False
        assert "Validator error" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_single_field_no_validator(self):
        """Testa validação quando não há validador para o tipo de campo."""
        result = await self.validation_service.validate_single_field("campo_desconhecido", "valor", "tipo_inexistente")

        assert result["success"] is False
        assert "No validator found" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_batch_with_error(self):
        """Testa validação em lote com erro em um registro."""
        # First record succeeds, second fails
        responses = [
            {
                "success": True,
                "is_valid": True,
                "validation_score": 0.9
            },
            Exception("Validation error")
        ]

        original_method = self.validation_service.validate_consultation_data
        call_count = 0
        
        async def mock_validate(data, context=None):
            nonlocal call_count
            response = responses[call_count]
            call_count += 1
            if isinstance(response, Exception):
                raise response
            return response

        self.validation_service.validate_consultation_data = mock_validate

        data_batch = [
            {"nome": "João Silva"},
            {"nome": "Maria Santos"}
        ]

        results = await self.validation_service.validate_batch(data_batch)

        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert "Validation error" in results[1]["error"]


class TestValidationServicePerformanceValidation:
    """Testes para validação de performance do ValidationService."""

    def setup_method(self):
        """Setup para cada teste."""
        self.validation_service = ValidationService()

    @pytest.mark.asyncio
    async def test_perform_comprehensive_validation(self):
        """Testa validação abrangente de dados."""
        # Mock validator responses
        valid_result = MagicMock(spec=ValidationResult)
        valid_result.is_valid = True
        valid_result.value = "normalized_value"
        valid_result.errors = []
        valid_result.confidence = 0.9
        
        self.validation_service.name_validator.validate.return_value = valid_result
        self.validation_service.phone_validator.validate.return_value = valid_result

        data = {
            "nome": "João Silva",
            "telefone": "11999888777",
            "campo_vazio": "",
            "campo_nulo": None
        }

        result = await self.validation_service._perform_comprehensive_validation(data)

        # Should only validate non-empty fields
        assert "nome" in result["field_validations"]
        assert "telefone" in result["field_validations"]
        assert "campo_vazio" not in result["field_validations"]
        assert "campo_nulo" not in result["field_validations"]
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_perform_comprehensive_validation_with_low_confidence(self):
        """Testa validação com baixa confiança."""
        low_confidence_result = MagicMock(spec=ValidationResult)
        low_confidence_result.is_valid = True
        low_confidence_result.value = "value"
        low_confidence_result.errors = []
        low_confidence_result.confidence = 0.6  # Low confidence

        self.validation_service.name_validator.validate.return_value = low_confidence_result

        data = {"nome": "João"}

        result = await self.validation_service._perform_comprehensive_validation(data)

        assert len(result["warnings"]) > 0
        assert any("confidence" in warning.lower() for warning in result["warnings"])