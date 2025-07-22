"""
Normalizador de dados unificado para consultas médicas.

Substitui o antigo data_normalizer.py, eliminando duplicação de lógica
e integrando com o novo sistema de validação modular.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.core.logging.logger_factory import get_logger
from ..validation_orchestrator import ValidationOrchestrator, ValidationSummary, ValidationMode
from ..validators.phone_validator import PhoneValidator
from ..validators.date_validator import DateValidator
from ..validators.name_validator import NameValidator
from ..validators.document_validator import DocumentValidator
from ..validators.base_validator import BaseValidator, ValidationResult
from .field_mapper import FieldMapper

logger = get_logger(__name__)


class PassThroughValidator(BaseValidator):
    """Simple validator that accepts any value without validation."""
    
    def validate(self, value: Any, **kwargs) -> ValidationResult:
        """Accept any non-empty value."""
        if not value:
            return ValidationResult(
                is_valid=False,
                value=None,
                confidence=0.0,
                errors=["Valor não pode ser vazio"],
                warnings=[],
                suggestions=[],
                metadata={}
            )
        
        return ValidationResult(
            is_valid=True,
            value=value,
            confidence=0.8,  # Medium confidence since no validation
            errors=[],
            warnings=[],
            suggestions=[],
            metadata={}
        )
    
    def normalize(self, value: Any) -> str:
        """Return value as-is."""
        return str(value) if value else ""


@dataclass
class NormalizationResult:
    """
    Resultado da normalização de dados.
    
    Attributes:
        success: True se normalização foi bem-sucedida
        normalized_data: Dados normalizados
        original_data: Dados originais fornecidos
        validation_summary: Resumo detalhado das validações
        field_mapping_info: Informações sobre mapeamento de campos
        confidence_score: Confiança geral na normalização (0.0-1.0)
        recommendations: Recomendações de melhoria
    """
    success: bool
    normalized_data: Dict[str, Any]
    original_data: Dict[str, Any]
    validation_summary: ValidationSummary
    field_mapping_info: Dict[str, Any]
    confidence_score: float
    recommendations: List[str]


class DataNormalizer:
    """
    Normalizador central de dados para consultas médicas.
    
    Integra validadores específicos e mapeamento de campos
    para fornecer normalização completa e consistente.
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Inicializa o normalizador.
        
        Args:
            strict_mode: Se True, falha na primeira validação inválida
        """
        self.strict_mode = strict_mode
        self.orchestrator = ValidationOrchestrator()
        self.field_mapper = FieldMapper()
        
        # Configura validadores
        self._setup_validators()
    
    def normalize_consultation_data(
        self, 
        data: Dict[str, Any],
        validation_mode: Optional[ValidationMode] = None
    ) -> NormalizationResult:
        """
        Normaliza dados completos de consulta médica.
        
        Args:
            data: Dicionário com dados da consulta
            validation_mode: Modo de validação (sobrescreve strict_mode)
            
        Returns:
            NormalizationResult com resultado completo
        """
        if not data:
            return self._create_error_result(
                {},
                "Dados vazios fornecidos",
                confidence=0.0
            )
        
        try:
            # Preserva dados originais
            original_data = data.copy()
            
            # Determina modo de validação
            if validation_mode is None:
                validation_mode = ValidationMode.STRICT if self.strict_mode else ValidationMode.PERMISSIVE
            
            # Analisa mapeamento de campos
            field_mapping_info = self.field_mapper.validate_field_names(data)
            
            # Mapeia campos para nomenclatura padrão
            mapped_data = self.field_mapper.map_data(data)
            logger.info(f"Data normalizer - Original data: {data}")
            logger.info(f"Data normalizer - Mapped data: {mapped_data}")
            
            # Valida dados mapeados
            required_fields = self.field_mapper.get_required_fields()
            validation_summary = self.orchestrator.validate_data(
                mapped_data,
                mode=validation_mode,
                required_fields=required_fields
            )
            
            # Gera recomendações
            recommendations = self._generate_recommendations(
                validation_summary,
                field_mapping_info,
                mapped_data
            )
            
            # Calcula confiança final
            confidence_score = self._calculate_final_confidence(
                validation_summary,
                field_mapping_info
            )
            
            # Determina sucesso
            success = validation_summary.is_valid and len(field_mapping_info["missing_required"]) == 0
            
            # Log final normalized data
            logger.info(f"Data normalizer - Final normalized data: {validation_summary.normalized_data}")
            
            return NormalizationResult(
                success=success,
                normalized_data=validation_summary.normalized_data,
                original_data=original_data,
                validation_summary=validation_summary,
                field_mapping_info=field_mapping_info,
                confidence_score=confidence_score,
                recommendations=recommendations
            )
            
        except Exception as e:
            return self._create_error_result(
                data,
                f"Erro interno na normalização: {str(e)}",
                confidence=0.0
            )
    
    def quick_normalize_field(
        self, 
        field_name: str, 
        value: Any,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Normaliza rapidamente um campo específico.
        
        Args:
            field_name: Nome do campo
            value: Valor a ser normalizado
            **kwargs: Parâmetros adicionais para validação
            
        Returns:
            Dict com resultado da normalização
        """
        try:
            # Mapeia nome do campo
            target_field = self.field_mapper.map_field_name(field_name)
            if not target_field:
                return {
                    "success": False,
                    "normalized_value": None,
                    "original_value": value,
                    "error": f"Campo não reconhecido: {field_name}"
                }
            
            # Valida campo
            result = self.orchestrator.validate_field(target_field, value, **kwargs)
            
            return {
                "success": result.is_valid,
                "normalized_value": result.value if result.is_valid else None,
                "original_value": value,
                "errors": result.errors,
                "warnings": result.warnings,
                "suggestions": result.suggestions,
                "confidence": result.confidence,
                "field_metadata": result.metadata
            }
            
        except Exception as e:
            return {
                "success": False,
                "normalized_value": None,
                "original_value": value,
                "error": f"Erro na normalização: {str(e)}"
            }
    
    def get_field_suggestions(self, field_name: str, invalid_value: Any) -> List[str]:
        """
        Gera sugestões para um campo com valor inválido.
        
        Args:
            field_name: Nome do campo
            invalid_value: Valor que falhou na validação
            
        Returns:
            Lista de sugestões de correção
        """
        try:
            target_field = self.field_mapper.map_field_name(field_name)
            if not target_field or target_field not in self.orchestrator._validators:
                return []
            
            validator = self.orchestrator._validators[target_field]
            return validator.suggest(invalid_value)
            
        except Exception:
            return []
    
    def validate_required_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida especificamente campos obrigatórios.
        
        Args:
            data: Dicionário com dados
            
        Returns:
            Dict com status de campos obrigatórios
        """
        field_validation = self.field_mapper.validate_field_names(data)
        required_fields = self.field_mapper.get_required_fields()
        
        result = {
            "all_present": len(field_validation["missing_required"]) == 0,
            "missing_fields": field_validation["missing_required"],
            "present_required": [],
            "field_aliases": {}
        }
        
        # Verifica quais campos obrigatórios estão presentes
        mapped_data = self.field_mapper.map_data(data)
        for required_field in required_fields:
            if required_field in mapped_data and mapped_data[required_field]:
                result["present_required"].append(required_field)
            
            # Adiciona aliases para cada campo
            result["field_aliases"][required_field] = self.field_mapper.get_field_aliases(required_field)
        
        return result
    
    def get_normalization_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre capacidades de normalização.
        
        Returns:
            Dict com informações do sistema
        """
        return {
            "validator_info": self.orchestrator.get_validator_info(),
            "field_mapping_info": self.field_mapper.get_mapping_info(),
            "required_fields": self.field_mapper.get_required_fields(),
            "strict_mode": self.strict_mode,
            "supported_data_types": [
                "consulta_medica", "nome", "telefone", "data", "cpf", "cep"
            ]
        }
    
    def _setup_validators(self) -> None:
        """Configura e registra todos os validadores."""
        
        # Registra validadores com pesos de confiança
        self.orchestrator.register_validator("name", NameValidator(), confidence_weight=1.0)
        self.orchestrator.register_validator("phone", PhoneValidator(), confidence_weight=1.2)
        self.orchestrator.register_validator("consultation_date", DateValidator(), confidence_weight=1.1)
        self.orchestrator.register_validator("consultation_time", PassThroughValidator(), confidence_weight=0.7)  # Use PassThrough validator for times
        self.orchestrator.register_validator("cpf", DocumentValidator("cpf"), confidence_weight=1.0)
        self.orchestrator.register_validator("postal_code", DocumentValidator("cep"), confidence_weight=0.7)
        
        # Registra mapeamentos de campos no orquestrador
        field_mappings = self.field_mapper.get_mapping_info()
        for target_field, mapping_info in field_mappings.items():
            for alias in mapping_info["all_accepted_names"]:
                self.orchestrator.register_field_mapping(alias, target_field)
    
    def _generate_recommendations(
        self,
        validation_summary: ValidationSummary,
        field_mapping_info: Dict[str, Any],
        mapped_data: Dict[str, Any]
    ) -> List[str]:
        """
        Gera recomendações de melhoria baseadas na validação.
        
        Args:
            validation_summary: Resumo da validação
            field_mapping_info: Informações de mapeamento
            mapped_data: Dados mapeados
            
        Returns:
            Lista de recomendações
        """
        recommendations = []
        
        # Recomendações para campos não mapeados
        if field_mapping_info["unmapped"]:
            recommendations.append(
                f"Campos não reconhecidos: {', '.join(field_mapping_info['unmapped'])}"
            )
        
        # Recomendações para campos obrigatórios
        if field_mapping_info["missing_required"]:
            recommendations.append(
                f"Adicionar campos obrigatórios: {', '.join(field_mapping_info['missing_required'])}"
            )
        
        # Recomendações baseadas em confiança
        if validation_summary.overall_confidence < 0.7:
            recommendations.append("Revisar qualidade dos dados fornecidos")
        
        # Recomendações específicas por campo
        for field_name, result in validation_summary.field_results.items():
            if not result.is_valid and result.suggestions:
                recommendations.append(
                    f"Para {field_name}: {result.suggestions[0]}"
                )
            elif result.warnings:
                recommendations.append(
                    f"Atenção {field_name}: {result.warnings[0]}"
                )
        
        return recommendations
    
    def _calculate_final_confidence(
        self,
        validation_summary: ValidationSummary,
        field_mapping_info: Dict[str, Any]
    ) -> float:
        """
        Calcula confiança final considerando validação e mapeamento.
        
        Args:
            validation_summary: Resumo da validação
            field_mapping_info: Informações de mapeamento
            
        Returns:
            Confiança final (0.0-1.0)
        """
        base_confidence = validation_summary.overall_confidence
        
        # Penaliza campos não mapeados
        unmapped_penalty = len(field_mapping_info["unmapped"]) * 0.1
        
        # Penaliza campos obrigatórios ausentes
        missing_penalty = len(field_mapping_info["missing_required"]) * 0.2
        
        # Calcula confiança final
        final_confidence = base_confidence - unmapped_penalty - missing_penalty
        
        return max(min(final_confidence, 1.0), 0.0)
    
    def _create_error_result(
        self,
        data: Dict[str, Any],
        error_message: str,
        confidence: float = 0.0
    ) -> NormalizationResult:
        """
        Cria resultado de erro padronizado.
        
        Args:
            data: Dados originais
            error_message: Mensagem de erro
            confidence: Confiança do resultado
            
        Returns:
            NormalizationResult de erro
        """
        from ..validation_orchestrator import ValidationSummary
        
        error_summary = ValidationSummary(
            is_valid=False,
            field_results={},
            overall_confidence=confidence,
            total_errors=1,
            total_warnings=0,
            normalized_data={},
            suggestions=[error_message]
        )
        
        return NormalizationResult(
            success=False,
            normalized_data={},
            original_data=data,
            validation_summary=error_summary,
            field_mapping_info={"mapped": [], "unmapped": [], "missing_required": []},
            confidence_score=confidence,
            recommendations=[error_message]
        )