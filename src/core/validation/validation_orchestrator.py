"""
Orquestrador central de validação do sistema.

Coordena todos os validadores específicos e fornece interface única
para validação de dados complexos como informações de consulta médica.
"""

from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass
from enum import Enum

from .validators.base_validator import BaseValidator, ValidationResult


class ValidationMode(Enum):
    """Modos de validação disponíveis."""
    STRICT = "strict"  # Falha na primeira validação inválida
    PERMISSIVE = "permissive"  # Continua validação mesmo com erros
    SUGGESTIONS_ONLY = "suggestions_only"  # Só gera sugestões, sem falhar


@dataclass
class ValidationSummary:
    """
    Resumo completo de validação de múltiplos campos.
    
    Attributes:
        is_valid: True se todas as validações passaram
        field_results: Dicionário com resultado por campo
        overall_confidence: Confiança geral (média ponderada)
        total_errors: Total de erros encontrados
        total_warnings: Total de avisos encontrados
        normalized_data: Dados normalizados
        suggestions: Sugestões gerais de melhoria
    """
    is_valid: bool
    field_results: Dict[str, ValidationResult]
    overall_confidence: float
    total_errors: int
    total_warnings: int  
    normalized_data: Dict[str, Any]
    suggestions: List[str]


class ValidationOrchestrator:
    """
    Coordenador principal de validação do sistema.
    
    Gerencia instâncias de validadores específicos e coordena
    validação de objetos complexos com múltiplos campos.
    """
    
    def __init__(self):
        """Inicializa o orquestrador com validadores padrão."""
        self._validators: Dict[str, BaseValidator] = {}
        self._field_mapping: Dict[str, str] = {}
        self._confidence_weights: Dict[str, float] = {}
        
    def register_validator(
        self, 
        field_name: str, 
        validator: BaseValidator,
        confidence_weight: float = 1.0
    ) -> None:
        """
        Registra um validador para um campo específico.
        
        Args:
            field_name: Nome do campo a ser validado
            validator: Instância do validador
            confidence_weight: Peso na confiança geral (padrão 1.0)
        """
        self._validators[field_name] = validator
        self._confidence_weights[field_name] = confidence_weight
        
    def register_field_mapping(self, source_field: str, target_field: str) -> None:
        """
        Registra mapeamento entre nomes de campos.
        
        Args:
            source_field: Nome do campo de entrada (ex: 'telefone')
            target_field: Nome do campo normalizado (ex: 'phone')
        """
        self._field_mapping[source_field] = target_field
    
    def validate_field(
        self, 
        field_name: str, 
        value: Any, 
        **kwargs
    ) -> ValidationResult:
        """
        Valida um campo específico.
        
        Args:
            field_name: Nome do campo
            value: Valor a ser validado
            **kwargs: Parâmetros adicionais para o validador
            
        Returns:
            ValidationResult do campo
            
        Raises:
            KeyError: Se o validador para o campo não estiver registrado
        """
        if field_name not in self._validators:
            raise KeyError(f"Validador não registrado para campo: {field_name}")
            
        validator = self._validators[field_name]
        return validator.validate(value, **kwargs)
    
    def validate_data(
        self, 
        data: Dict[str, Any],
        mode: ValidationMode = ValidationMode.PERMISSIVE,
        required_fields: Optional[List[str]] = None
    ) -> ValidationSummary:
        """
        Valida um objeto completo com múltiplos campos.
        
        Args:
            data: Dicionário com dados a serem validados
            mode: Modo de validação (strict/permissive/suggestions_only)
            required_fields: Lista de campos obrigatórios
            
        Returns:
            ValidationSummary com resultado completo
        """
        if not data:
            return ValidationSummary(
                is_valid=False,
                field_results={},
                overall_confidence=0.0,
                total_errors=1,
                total_warnings=0,
                normalized_data={},
                suggestions=["Dados vazios fornecidos"]
            )
        
        field_results = {}
        normalized_data = {}
        total_errors = 0
        total_warnings = 0
        confidence_scores = []
        general_suggestions = []
        
        # Aplica mapeamento de campos
        mapped_data = self._apply_field_mapping(data)
        
        # Valida campos obrigatórios
        if required_fields:
            missing_fields = [
                field for field in required_fields 
                if field not in mapped_data or not mapped_data[field]
            ]
            if missing_fields:
                total_errors += len(missing_fields)
                general_suggestions.append(
                    f"Campos obrigatórios ausentes: {', '.join(missing_fields)}"
                )
                if mode == ValidationMode.STRICT:
                    return ValidationSummary(
                        is_valid=False,
                        field_results={},
                        overall_confidence=0.0,
                        total_errors=total_errors,
                        total_warnings=0,
                        normalized_data={},
                        suggestions=general_suggestions
                    )
        
        # Valida cada campo com validador registrado
        for field_name, value in mapped_data.items():
            if field_name not in self._validators:
                continue
                
            try:
                result = self.validate_field(field_name, value)
                field_results[field_name] = result
                
                if result.is_valid:
                    normalized_data[field_name] = result.value
                    confidence_scores.append(
                        result.confidence * self._confidence_weights.get(field_name, 1.0)
                    )
                else:
                    total_errors += len(result.errors)
                    if mode == ValidationMode.STRICT:
                        return ValidationSummary(
                            is_valid=False,
                            field_results=field_results,
                            overall_confidence=0.0,
                            total_errors=total_errors,
                            total_warnings=total_warnings,
                            normalized_data={},
                            suggestions=result.suggestions + general_suggestions
                        )
                
                total_warnings += len(result.warnings)
                
            except Exception as e:
                error_result = ValidationResult(
                    is_valid=False,
                    original_value=value,
                    errors=[f"Erro interno na validação: {str(e)}"],
                    confidence=0.0
                )
                field_results[field_name] = error_result
                total_errors += 1
        
        # Calcula confiança geral
        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores) 
            if confidence_scores else 0.0
        )
        
        # Determina se validação geral passou
        is_valid = (
            total_errors == 0 if mode != ValidationMode.SUGGESTIONS_ONLY 
            else True
        )
        
        return ValidationSummary(
            is_valid=is_valid,
            field_results=field_results,
            overall_confidence=overall_confidence,
            total_errors=total_errors,
            total_warnings=total_warnings,
            normalized_data=normalized_data,
            suggestions=general_suggestions
        )
    
    def suggest_corrections(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Gera sugestões de correção para dados inválidos.
        
        Args:
            data: Dados a serem analisados
            
        Returns:
            Dicionário com sugestões por campo
        """
        suggestions = {}
        mapped_data = self._apply_field_mapping(data)
        
        for field_name, value in mapped_data.items():
            if field_name in self._validators:
                validator = self._validators[field_name]
                field_suggestions = validator.suggest(value)
                if field_suggestions:
                    suggestions[field_name] = field_suggestions
                    
        return suggestions
    
    def get_validator_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna informações sobre validadores registrados.
        
        Returns:
            Dicionário com informações dos validadores
        """
        info = {}
        for field_name, validator in self._validators.items():
            info[field_name] = {
                'validator_class': validator.__class__.__name__,
                'validation_rules': validator.get_validation_rules(),
                'confidence_weight': self._confidence_weights.get(field_name, 1.0)
            }
        return info
    
    def _apply_field_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica mapeamento de nomes de campos.
        
        Args:
            data: Dados originais
            
        Returns:
            Dados com campos mapeados
        """
        mapped_data = {}
        for field_name, value in data.items():
            target_field = self._field_mapping.get(field_name, field_name)
            mapped_data[target_field] = value
        return mapped_data