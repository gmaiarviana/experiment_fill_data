"""
Módulo de validação unificado.

Este módulo centraliza todas as validações e normalizações do sistema,
eliminando a duplicação de lógica presente em múltiplos arquivos.
"""

from .validation_orchestrator import ValidationOrchestrator
from .validators.phone_validator import PhoneValidator
from .validators.date_validator import DateValidator
from .validators.name_validator import NameValidator
from .validators.document_validator import DocumentValidator
from .normalizers.data_normalizer import DataNormalizer
from .normalizers.field_mapper import FieldMapper

__all__ = [
    'ValidationOrchestrator',
    'PhoneValidator',
    'DateValidator', 
    'NameValidator',
    'DocumentValidator',
    'DataNormalizer',
    'FieldMapper'
]