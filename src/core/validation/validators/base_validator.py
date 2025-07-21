"""
Classe base abstrata para todos os validadores do sistema.

Define a interface comum que todos os validadores devem implementar,
garantindo consistência e facilitando extensibilidade.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """
    Resultado padronizado de validação.
    
    Attributes:
        is_valid: True se a validação passou
        value: Valor validado/normalizado 
        original_value: Valor original fornecido
        errors: Lista de erros encontrados
        warnings: Lista de avisos (não impedem validação)
        suggestions: Lista de sugestões para correção
        confidence: Nível de confiança da validação (0.0-1.0)
        metadata: Metadados adicionais específicos do validador
    """
    is_valid: bool
    value: Any = None
    original_value: Any = None
    errors: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Inicializa listas vazias se None."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []
        if self.metadata is None:
            self.metadata = {}


class BaseValidator(ABC):
    """
    Classe base abstrata para todos os validadores.
    
    Define a interface comum que todos os validadores devem implementar,
    incluindo métodos para validação, normalização e geração de sugestões.
    """
    
    @abstractmethod
    def validate(self, value: Any, **kwargs) -> ValidationResult:
        """
        Valida um valor de entrada.
        
        Args:
            value: Valor a ser validado
            **kwargs: Parâmetros adicionais específicos do validador
            
        Returns:
            ValidationResult com resultado da validação
        """
        pass
    
    @abstractmethod
    def normalize(self, value: Any, **kwargs) -> Any:
        """
        Normaliza um valor de entrada.
        
        Args:
            value: Valor a ser normalizado
            **kwargs: Parâmetros adicionais específicos do validador
            
        Returns:
            Valor normalizado
        """
        pass
    
    def suggest(self, value: Any, **kwargs) -> List[str]:
        """
        Gera sugestões de correção para um valor inválido.
        
        Args:
            value: Valor que falhou na validação
            **kwargs: Parâmetros adicionais específicos do validador
            
        Returns:
            Lista de sugestões de correção
        """
        return []
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Retorna as regras de validação aplicadas por este validador.
        
        Returns:
            Dicionário com as regras de validação
        """
        return {}
    
    def batch_validate(self, values: List[Any], **kwargs) -> List[ValidationResult]:
        """
        Valida uma lista de valores em lote.
        
        Args:
            values: Lista de valores a serem validados
            **kwargs: Parâmetros adicionais específicos do validador
            
        Returns:
            Lista de ValidationResult para cada valor
        """
        results = []
        for value in values:
            try:
                result = self.validate(value, **kwargs)
                results.append(result)
            except Exception as e:
                results.append(ValidationResult(
                    is_valid=False,
                    value=None,
                    original_value=value,
                    errors=[f"Erro na validação: {str(e)}"],
                    confidence=0.0
                ))
        return results
    
    def _create_error_result(
        self, 
        value: Any, 
        errors: List[str], 
        suggestions: List[str] = None,
        confidence: float = 0.0
    ) -> ValidationResult:
        """
        Cria um ValidationResult de erro padronizado.
        
        Args:
            value: Valor original que falhou
            errors: Lista de erros
            suggestions: Lista de sugestões opcionais
            confidence: Nível de confiança
            
        Returns:
            ValidationResult de erro
        """
        return ValidationResult(
            is_valid=False,
            value=None,
            original_value=value,
            errors=errors,
            suggestions=suggestions or [],
            confidence=confidence
        )
    
    def _create_success_result(
        self, 
        original_value: Any,
        normalized_value: Any = None,
        warnings: List[str] = None,
        confidence: float = 1.0,
        metadata: Dict[str, Any] = None
    ) -> ValidationResult:
        """
        Cria um ValidationResult de sucesso padronizado.
        
        Args:
            original_value: Valor original fornecido
            normalized_value: Valor normalizado (default: original_value)
            warnings: Lista de avisos opcionais
            confidence: Nível de confiança
            metadata: Metadados adicionais
            
        Returns:
            ValidationResult de sucesso
        """
        return ValidationResult(
            is_valid=True,
            value=normalized_value if normalized_value is not None else original_value,
            original_value=original_value,
            warnings=warnings or [],
            confidence=confidence,
            metadata=metadata or {}
        )