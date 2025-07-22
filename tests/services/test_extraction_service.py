import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from src.services.extraction_service import ExtractionService
from src.core.entity_extraction import EntityExtractor
from src.core.validation.normalizers.data_normalizer import DataNormalizer, NormalizationResult, ValidationSummary


class TestExtractionService:
    """Testes para o serviço de extração."""

    def setup_method(self):
        """Setup para cada teste."""
        self.mock_entity_extractor = AsyncMock(spec=EntityExtractor)
        self.extraction_service = ExtractionService(entity_extractor=self.mock_entity_extractor)

    @patch('src.services.extraction_service.get_entity_extractor')
    def test_extraction_service_initialization(self, mock_get_extractor):
        """Testa inicialização do ExtractionService."""
        mock_extractor = MagicMock(spec=EntityExtractor)
        mock_get_extractor.return_value = mock_extractor
        
        service = ExtractionService()
        
        assert service.entity_extractor == mock_extractor
        assert service.data_normalizer is not None
        assert service.validation_orchestrator is not None

    @pytest.mark.asyncio
    async def test_extract_entities_success(self):
        """Testa extração de entidades bem-sucedida."""
        # Setup mock responses
        extraction_result = {
            "success": True,
            "extracted_data": {
                "nome": "João Silva",
                "telefone": "11999888777",
                "data": "2025-07-25",
                "horario": "14:00",
                "tipo_consulta": "cardiologia"
            },
            "confidence_score": 0.9
        }
        
        self.mock_entity_extractor.extract_consulta_entities.return_value = extraction_result
        
        # Mock data normalizer
        mock_validation_summary = MagicMock(spec=ValidationSummary)
        mock_validation_summary.field_results = {}
        
        mock_normalization_result = MagicMock(spec=NormalizationResult)
        mock_normalization_result.normalized_data = extraction_result["extracted_data"]
        mock_normalization_result.validation_summary = mock_validation_summary
        
        self.extraction_service.data_normalizer.normalize_consultation_data.return_value = mock_normalization_result

        # Execute
        result = await self.extraction_service.extract_entities("João Silva, telefone 11999888777, consulta de cardiologia para 25/07 às 14h")

        # Assert
        assert result["success"] is True
        assert result["extracted_data"]["nome"] == "João Silva"
        assert result["confidence_score"] > 0.9
        assert "quality_metrics" in result
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_extract_entities_with_context(self):
        """Testa extração de entidades com contexto."""
        context = {
            "extracted_data": {
                "nome": "João Silva",
                "telefone": "11999888777"
            }
        }
        
        extraction_result = {
            "success": True,
            "extracted_data": {
                "nome": "João Silva",
                "telefone": "11999888777",
                "data": "2025-07-25",
                "horario": "14:00"
            },
            "confidence_score": 0.8
        }
        
        self.mock_entity_extractor.extract_consulta_entities.return_value = extraction_result
        
        # Mock data normalizer
        mock_validation_summary = MagicMock(spec=ValidationSummary)
        mock_validation_summary.field_results = {}
        
        mock_normalization_result = MagicMock(spec=NormalizationResult)
        mock_normalization_result.normalized_data = extraction_result["extracted_data"]
        mock_normalization_result.validation_summary = mock_validation_summary
        
        self.extraction_service.data_normalizer.normalize_consultation_data.return_value = mock_normalization_result

        # Execute
        result = await self.extraction_service.extract_entities("consulta para amanhã às 14h", context)

        # Assert
        assert result["success"] is True
        assert result["confidence_score"] > 0.8  # Should be boosted due to context
        assert result["metadata"]["context_used"] is True

    @pytest.mark.asyncio
    async def test_extract_entities_extraction_failure(self):
        """Testa falha na extração de entidades."""
        extraction_result = {
            "success": False,
            "error": "Failed to extract entities"
        }
        
        self.mock_entity_extractor.extract_consulta_entities.return_value = extraction_result

        result = await self.extraction_service.extract_entities("Mensagem confusa")

        assert result["success"] is False
        assert result["error"] == "Failed to extract entities"
        assert result["confidence_score"] == 0.0

    @pytest.mark.asyncio
    async def test_extract_entities_batch_success(self):
        """Testa extração em lote bem-sucedida."""
        messages = [
            "João Silva, telefone 11999888777",
            "Consulta para 25/07 às 14h"
        ]
        
        extraction_results = [
            {
                "success": True,
                "extracted_data": {
                    "nome": "João Silva",
                    "telefone": "11999888777"
                },
                "confidence_score": 0.8
            },
            {
                "success": True,
                "extracted_data": {
                    "data": "2025-07-25",
                    "horario": "14:00"
                },
                "confidence_score": 0.7
            }
        ]
        
        self.mock_entity_extractor.extract_consulta_entities.side_effect = extraction_results
        
        # Mock data normalizer
        mock_validation_summary = MagicMock(spec=ValidationSummary)
        mock_validation_summary.field_results = {}
        
        mock_normalization_result = MagicMock(spec=NormalizationResult)
        mock_normalization_result.validation_summary = mock_validation_summary
        
        def mock_normalize(data):
            result = MagicMock(spec=NormalizationResult)
            result.normalized_data = data
            result.validation_summary = mock_validation_summary
            return result
        
        self.extraction_service.data_normalizer.normalize_consultation_data.side_effect = mock_normalize

        results = await self.extraction_service.extract_entities_batch(messages)

        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[1]["success"] is True
        assert results[0]["message_index"] == 0
        assert results[1]["message_index"] == 1

    @pytest.mark.asyncio
    async def test_extract_entities_batch_with_error(self):
        """Testa extração em lote com erro em uma mensagem."""
        messages = [
            "João Silva, telefone 11999888777",
            "Mensagem que causará erro"
        ]
        
        extraction_results = [
            {
                "success": True,
                "extracted_data": {"nome": "João Silva", "telefone": "11999888777"},
                "confidence_score": 0.8
            },
            Exception("Erro na extração")
        ]
        
        self.mock_entity_extractor.extract_consulta_entities.side_effect = extraction_results
        
        # Mock data normalizer
        mock_validation_summary = MagicMock(spec=ValidationSummary)
        mock_validation_summary.field_results = {}
        
        mock_normalization_result = MagicMock(spec=NormalizationResult)
        mock_normalization_result.normalized_data = {"nome": "João Silva", "telefone": "11999888777"}
        mock_normalization_result.validation_summary = mock_validation_summary
        
        self.extraction_service.data_normalizer.normalize_consultation_data.return_value = mock_normalization_result

        results = await self.extraction_service.extract_entities_batch(messages)

        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert "Erro na extração" in results[1]["error"]

    def test_enhance_message_with_context(self):
        """Testa aprimoramento de mensagem com contexto."""
        context = {
            "extracted_data": {
                "nome": "João Silva",
                "telefone": "11999888777",
                "tipo_consulta": "cardiologia"
            }
        }
        
        enhanced_message = self.extraction_service._enhance_message_with_context(
            "consulta para amanhã às 14h", 
            context
        )
        
        assert "Contexto:" in enhanced_message
        assert "Paciente: João Silva" in enhanced_message
        assert "Telefone: 11999888777" in enhanced_message
        assert "Tipo de consulta: cardiologia" in enhanced_message
        assert "consulta para amanhã às 14h" in enhanced_message

    def test_enhance_message_without_context(self):
        """Testa que mensagem não é modificada sem contexto."""
        original_message = "João Silva, consulta para amanhã"
        enhanced_message = self.extraction_service._enhance_message_with_context(original_message, None)
        
        assert enhanced_message == original_message

    def test_enhance_message_with_empty_context(self):
        """Testa mensagem com contexto vazio."""
        context = {"extracted_data": {}}
        original_message = "João Silva, consulta para amanhã"
        enhanced_message = self.extraction_service._enhance_message_with_context(original_message, context)
        
        assert enhanced_message == original_message

    @pytest.mark.asyncio
    async def test_validate_and_normalize_data_success(self):
        """Testa validação e normalização bem-sucedida."""
        extracted_data = {
            "nome": "joão silva",
            "telefone": "11999888777",
            "data": "2025-07-25"
        }
        
        # Mock successful normalization
        mock_field_result = MagicMock()
        mock_field_result.is_valid = True
        
        mock_validation_summary = MagicMock(spec=ValidationSummary)
        mock_validation_summary.field_results = {
            "nome": mock_field_result,
            "telefone": mock_field_result,
            "data": mock_field_result
        }
        
        mock_normalization_result = MagicMock(spec=NormalizationResult)
        mock_normalization_result.normalized_data = {
            "nome": "João Silva",
            "telefone": "(11) 99988-8777",
            "data": "2025-07-25"
        }
        mock_normalization_result.validation_summary = mock_validation_summary
        
        self.extraction_service.data_normalizer.normalize_consultation_data.return_value = mock_normalization_result

        result = await self.extraction_service._validate_and_normalize_data(extracted_data)

        assert result["normalized_data"]["nome"] == "João Silva"
        assert result["validation_summary"]["is_valid"] is True
        assert len(result["validation_summary"]["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_and_normalize_data_with_errors(self):
        """Testa validação e normalização com erros."""
        extracted_data = {
            "nome": "j",  # Nome muito curto
            "telefone": "123",  # Telefone inválido
            "data": "ontem"  # Data inválida
        }
        
        # Mock validation with errors
        mock_field_result_valid = MagicMock()
        mock_field_result_valid.is_valid = True
        
        mock_field_result_invalid = MagicMock()
        mock_field_result_invalid.is_valid = False
        mock_field_result_invalid.error_message = "Campo inválido"
        
        mock_validation_summary = MagicMock(spec=ValidationSummary)
        mock_validation_summary.field_results = {
            "nome": mock_field_result_invalid,
            "telefone": mock_field_result_invalid,
            "data": mock_field_result_valid
        }
        
        mock_normalization_result = MagicMock(spec=NormalizationResult)
        mock_normalization_result.normalized_data = extracted_data
        mock_normalization_result.validation_summary = mock_validation_summary
        
        self.extraction_service.data_normalizer.normalize_consultation_data.return_value = mock_normalization_result

        result = await self.extraction_service._validate_and_normalize_data(extracted_data)

        assert result["validation_summary"]["is_valid"] is False
        assert len(result["validation_summary"]["errors"]) > 0

    def test_calculate_final_confidence_valid_data(self):
        """Testa cálculo de confiança com dados válidos."""
        validation_result = {
            "validation_summary": {
                "is_valid": True,
                "errors": []
            }
        }
        
        context = {
            "extracted_data": {
                "nome": "João Silva",
                "telefone": "11999888777"
            }
        }

        final_confidence = self.extraction_service._calculate_final_confidence(0.8, validation_result, context)

        assert final_confidence > 0.8  # Should be boosted
        assert final_confidence <= 1.0

    def test_calculate_final_confidence_invalid_data(self):
        """Testa cálculo de confiança com dados inválidos."""
        validation_result = {
            "validation_summary": {
                "is_valid": False,
                "errors": ["Nome inválido"]
            }
        }

        final_confidence = self.extraction_service._calculate_final_confidence(0.8, validation_result)

        assert final_confidence < 0.8  # Should be reduced
        assert final_confidence >= 0.0

    def test_calculate_quality_metrics(self):
        """Testa cálculo de métricas de qualidade."""
        extracted_data = {
            "nome": "João Silva",
            "telefone": "11999888777",
            "data": None,
            "horario": "",
            "tipo_consulta": "cardiologia"
        }
        
        # Mock validation result
        mock_field_result_valid = MagicMock()
        mock_field_result_valid.is_valid = True
        
        mock_field_result_invalid = MagicMock()
        mock_field_result_invalid.is_valid = False
        
        validation_result = {
            "validation_summary": {
                "errors": ["Erro 1"],
                "field_results": {
                    "nome": mock_field_result_valid,
                    "telefone": mock_field_result_valid,
                    "data": mock_field_result_invalid,
                    "horario": mock_field_result_invalid,
                    "tipo_consulta": mock_field_result_valid
                }
            }
        }

        metrics = self.extraction_service._calculate_quality_metrics(extracted_data, validation_result)

        assert metrics["total_fields"] == 5
        assert metrics["filled_fields"] == 3  # nome, telefone, tipo_consulta
        assert metrics["valid_fields"] == 3  # nome, telefone, tipo_consulta
        assert metrics["completeness"] == 0.6  # 3/5
        assert metrics["validity"] == 0.6  # 3/5
        assert metrics["validation_errors"] == 1

    def test_create_extraction_error_result(self):
        """Testa criação de resultado de erro."""
        error_message = "Falha na extração"
        
        result = self.extraction_service._create_extraction_error_result(error_message)

        assert result["success"] is False
        assert result["error"] == error_message
        assert result["confidence_score"] == 0.0
        assert result["quality_metrics"]["completeness"] == 0.0
        assert result["validation_summary"]["is_valid"] is False

    def test_create_extraction_error_result_with_message_index(self):
        """Testa criação de resultado de erro com índice da mensagem."""
        result = self.extraction_service._create_extraction_error_result("Erro", message_index=1)

        assert result["message_index"] == 1

    def test_get_extraction_schema(self):
        """Testa obtenção do schema de extração."""
        expected_schema = {
            "name": "extract_consultation",
            "parameters": {
                "properties": {
                    "nome": {"type": "string"},
                    "telefone": {"type": "string"}
                }
            }
        }
        
        self.mock_entity_extractor.get_schema.return_value = expected_schema

        schema = self.extraction_service.get_extraction_schema()

        assert schema == expected_schema

    def test_get_supported_entities(self):
        """Testa obtenção das entidades suportadas."""
        schema = {
            "name": "extract_consultation",
            "parameters": {
                "properties": {
                    "nome": {"type": "string"},
                    "telefone": {"type": "string"},
                    "data": {"type": "string"},
                    "horario": {"type": "string"}
                }
            }
        }
        
        self.mock_entity_extractor.get_schema.return_value = schema

        entities = self.extraction_service.get_supported_entities()

        assert "nome" in entities
        assert "telefone" in entities
        assert "data" in entities
        assert "horario" in entities
        assert len(entities) == 4

    def test_get_supported_entities_no_schema(self):
        """Testa obtenção das entidades quando schema não está disponível."""
        self.mock_entity_extractor.get_schema.return_value = {}

        entities = self.extraction_service.get_supported_entities()

        assert entities == []


class TestExtractionServiceErrorHandling:
    """Testes para tratamento de erros no ExtractionService."""

    def setup_method(self):
        """Setup para cada teste."""
        self.mock_entity_extractor = AsyncMock(spec=EntityExtractor)
        self.extraction_service = ExtractionService(entity_extractor=self.mock_entity_extractor)

    @pytest.mark.asyncio
    async def test_extract_entities_general_exception(self):
        """Testa tratamento de exceção geral na extração."""
        self.mock_entity_extractor.extract_consulta_entities.side_effect = Exception("Erro inesperado")

        result = await self.extraction_service.extract_entities("Teste")

        assert result["success"] is False
        assert "Erro inesperado" in result["error"]
        assert result["confidence_score"] == 0.0

    @pytest.mark.asyncio
    async def test_validate_and_normalize_exception(self):
        """Testa tratamento de exceção na validação e normalização."""
        extracted_data = {"nome": "João Silva"}
        
        self.extraction_service.data_normalizer.normalize_consultation_data.side_effect = Exception("Erro de validação")

        result = await self.extraction_service._validate_and_normalize_data(extracted_data)

        assert result["normalized_data"] == extracted_data
        assert result["validation_summary"]["is_valid"] is False
        assert "Erro de validação" in result["validation_summary"]["errors"][0]