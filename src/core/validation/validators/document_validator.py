"""
Validador especializado para documentos brasileiros (CPF, CEP, etc.).

Migrado de src/core/validators.py para eliminar duplicação de lógica.
Implementa validação e formatação de documentos oficiais brasileiros
com algoritmos de verificação apropriados.
"""

import re
from typing import Any, List

from .base_validator import BaseValidator, ValidationResult


class DocumentValidator(BaseValidator):
    """
    Validador para documentos brasileiros.
    
    Suporta:
    - CPF: validação com dígitos verificadores
    - CEP: validação de formato brasileiro  
    - Formatação automática
    - Detecção de padrões inválidos (todos dígitos iguais)
    - Sugestões de correção
    """
    
    def __init__(self, document_type: str = "cpf"):
        """
        Inicializa o validador de documentos.
        
        Args:
            document_type: Tipo de documento ("cpf", "cep", "auto")
                          "auto" tenta detectar automaticamente
        """
        self.document_type = document_type.lower()
        
        # Padrões conhecidos de CPF inválido
        self.invalid_cpf_patterns = [
            '00000000000', '11111111111', '22222222222', '33333333333',
            '44444444444', '55555555555', '66666666666', '77777777777',
            '88888888888', '99999999999'
        ]
    
    def validate(self, value: Any, **kwargs) -> ValidationResult:
        """
        Valida documento brasileiro.
        
        Args:
            value: Documento a ser validado
            **kwargs: Parâmetros adicionais
                     - document_type: sobrescreve document_type
                     
        Returns:
            ValidationResult com resultado da validação
        """
        if not value:
            return self._create_error_result(
                value,
                ["Documento não pode ser vazio"],
                suggestions=self._generate_document_suggestions()
            )
        
        try:
            doc_str = str(value).strip()
            doc_type = kwargs.get("document_type", self.document_type)
            
            # Auto-detecção do tipo de documento
            if doc_type == "auto":
                doc_type = self._detect_document_type(doc_str)
            
            # Valida baseado no tipo
            if doc_type == "cpf":
                return self._validate_cpf(value, doc_str)
            elif doc_type == "cep":
                return self._validate_cep(value, doc_str)
            else:
                return self._create_error_result(
                    value,
                    [f"Tipo de documento não suportado: {doc_type}"],
                    suggestions=["Use 'cpf' ou 'cep'"]
                )
                
        except Exception as e:
            return self._create_error_result(
                value,
                [f"Erro na validação: {str(e)}"],
                suggestions=self._generate_document_suggestions()
            )
    
    def normalize(self, value: Any, **kwargs) -> str:
        """
        Normaliza documento para formato padrão.
        
        Args:
            value: Documento a ser normalizado
            **kwargs: Parâmetros adicionais
            
        Returns:
            Documento normalizado ou string vazia se inválido
        """
        result = self.validate(value, **kwargs)
        return result.value if result.is_valid else ""
    
    def suggest(self, value: Any, **kwargs) -> List[str]:
        """
        Gera sugestões de documentos válidos.
        
        Args:
            value: Documento que falhou na validação
            **kwargs: Parâmetros adicionais
            
        Returns:
            Lista de sugestões de documentos
        """
        if not value:
            return self._generate_document_suggestions()
        
        try:
            doc_str = str(value).strip()
            digits_only = re.sub(r'\D', '', doc_str)
            doc_type = kwargs.get("document_type", self.document_type)
            
            if doc_type == "auto":
                doc_type = self._detect_document_type(doc_str)
            
            suggestions = []
            
            if doc_type == "cpf":
                suggestions = self._suggest_cpf_corrections(digits_only)
            elif doc_type == "cep":
                suggestions = self._suggest_cep_corrections(digits_only)
            
            if not suggestions:
                suggestions = self._generate_document_suggestions()
                
            return suggestions[:5]  # Limita a 5 sugestões
            
        except Exception:
            return self._generate_document_suggestions()
    
    def get_validation_rules(self) -> dict:
        """
        Retorna regras de validação aplicadas.
        
        Returns:
            Dicionário com regras de validação
        """
        return {
            "document_type": self.document_type,
            "cpf": {
                "digits": 11,
                "format": "XXX.XXX.XXX-XX",
                "has_check_digits": True,
                "invalid_patterns": self.invalid_cpf_patterns
            },
            "cep": {
                "digits": 8,
                "format": "XXXXX-XXX",
                "has_check_digits": False
            }
        }
    
    def _validate_cpf(self, original_value: Any, cpf_str: str) -> ValidationResult:
        """
        Valida CPF brasileiro.
        
        Args:
            original_value: Valor original fornecido
            cpf_str: String do CPF
            
        Returns:
            ValidationResult para CPF
        """
        # Remove caracteres não numéricos
        digits = re.sub(r'\D', '', cpf_str)
        
        # Verifica se tem 11 dígitos
        if len(digits) != 11:
            return self._create_error_result(
                original_value,
                ["CPF deve ter 11 dígitos"],
                suggestions=["123.456.789-10", "987.654.321-00"]
            )
        
        # Verifica padrões inválidos (todos os dígitos iguais)
        if digits in self.invalid_cpf_patterns:
            return self._create_error_result(
                original_value,
                ["CPF inválido (todos os dígitos iguais)"],
                suggestions=["123.456.789-10", "987.654.321-00"]
            )
        
        # Calcula e valida dígitos verificadores
        if not self._validate_cpf_check_digits(digits):
            return self._create_error_result(
                original_value,
                ["CPF inválido (dígitos verificadores incorretos)"],
                suggestions=["123.456.789-10", "987.654.321-00"]
            )
        
        # Formata o CPF
        formatted = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
        
        return self._create_success_result(
            original_value=original_value,
            normalized_value=formatted,
            confidence=1.0,
            metadata={
                "document_type": "cpf",
                "digits_only": digits,
                "is_formatted": cpf_str != digits
            }
        )
    
    def _validate_cep(self, original_value: Any, cep_str: str) -> ValidationResult:
        """
        Valida CEP brasileiro.
        
        Args:
            original_value: Valor original fornecido
            cep_str: String do CEP
            
        Returns:
            ValidationResult para CEP
        """
        # Remove caracteres não numéricos
        digits = re.sub(r'\D', '', cep_str)
        
        # Verifica se tem 8 dígitos
        if len(digits) != 8:
            return self._create_error_result(
                original_value,
                ["CEP deve ter 8 dígitos"],
                suggestions=["01234-567", "12345-678", "98765-432"]
            )
        
        # Formata o CEP
        formatted = f"{digits[:5]}-{digits[5:]}"
        
        # Validações adicionais
        warnings = []
        confidence = 1.0
        
        # Verifica padrões suspeitos
        if digits == "00000000":
            warnings.append("CEP com todos os dígitos zero pode ser inválido")
            confidence = 0.7
        elif len(set(digits)) == 1:
            warnings.append("CEP com todos os dígitos iguais é incomum")
            confidence = 0.8
        
        return self._create_success_result(
            original_value=original_value,
            normalized_value=formatted,
            warnings=warnings,
            confidence=confidence,
            metadata={
                "document_type": "cep",
                "digits_only": digits,
                "is_formatted": cep_str != digits,
                "region_code": digits[:2]  # Primeiros 2 dígitos indicam região
            }
        )
    
    def _validate_cpf_check_digits(self, digits: str) -> bool:
        """
        Valida dígitos verificadores do CPF.
        
        Args:
            digits: String com 11 dígitos do CPF
            
        Returns:
            True se os dígitos verificadores estão corretos
        """
        try:
            # Calcula primeiro dígito verificador
            sum1 = sum(int(digits[i]) * (10 - i) for i in range(9))
            remainder1 = sum1 % 11
            digit1 = 0 if remainder1 < 2 else 11 - remainder1
            
            # Calcula segundo dígito verificador
            sum2 = sum(int(digits[i]) * (11 - i) for i in range(10))
            remainder2 = sum2 % 11
            digit2 = 0 if remainder2 < 2 else 11 - remainder2
            
            # Verifica se os dígitos verificadores estão corretos
            return int(digits[9]) == digit1 and int(digits[10]) == digit2
            
        except (ValueError, IndexError):
            return False
    
    def _detect_document_type(self, doc_str: str) -> str:
        """
        Detecta automaticamente o tipo de documento.
        
        Args:
            doc_str: String do documento
            
        Returns:
            Tipo detectado ("cpf", "cep", "unknown")
        """
        digits = re.sub(r'\D', '', doc_str)
        
        if len(digits) == 11:
            return "cpf"
        elif len(digits) == 8:
            return "cep"
        else:
            return "unknown"
    
    def _suggest_cpf_corrections(self, digits: str) -> List[str]:
        """
        Sugere correções para CPF inválido.
        
        Args:
            digits: Dígitos do CPF
            
        Returns:
            Lista de sugestões de CPF
        """
        suggestions = []
        
        # Se tem dígitos demais ou de menos, sugere exemplos válidos
        if len(digits) != 11:
            suggestions = ["123.456.789-10", "987.654.321-00", "456.789.123-45"]
        
        # Se tem 11 dígitos mas é inválido, tenta corrigir
        elif len(digits) == 11:
            # Se é padrão inválido, sugere válidos
            if digits in self.invalid_cpf_patterns:
                suggestions = ["123.456.789-10", "987.654.321-00"]
            
            # Se só os dígitos verificadores estão errados, tenta corrigir
            elif not self._validate_cpf_check_digits(digits):
                base_digits = digits[:9]
                corrected_cpf = self._generate_valid_cpf(base_digits)
                if corrected_cpf:
                    suggestions.append(corrected_cpf)
        
        return suggestions
    
    def _suggest_cep_corrections(self, digits: str) -> List[str]:
        """
        Sugere correções para CEP inválido.
        
        Args:
            digits: Dígitos do CEP
            
        Returns:
            Lista de sugestões de CEP
        """
        suggestions = []
        
        # Se tem dígitos demais ou de menos, sugere exemplos
        if len(digits) != 8:
            suggestions = ["01234-567", "12345-678", "98765-432"]
        
        # Se tem 8 dígitos válidos, formata
        elif len(digits) == 8:
            formatted = f"{digits[:5]}-{digits[5:]}"
            suggestions.append(formatted)
        
        return suggestions
    
    def _generate_valid_cpf(self, base_digits: str) -> str:
        """
        Gera CPF válido com base nos 9 primeiros dígitos.
        
        Args:
            base_digits: Primeiros 9 dígitos do CPF
            
        Returns:
            CPF válido formatado ou None se erro
        """
        try:
            if len(base_digits) != 9:
                return None
            
            # Calcula primeiro dígito verificador
            sum1 = sum(int(base_digits[i]) * (10 - i) for i in range(9))
            remainder1 = sum1 % 11
            digit1 = 0 if remainder1 < 2 else 11 - remainder1
            
            # Calcula segundo dígito verificador
            digits_with_first = base_digits + str(digit1)
            sum2 = sum(int(digits_with_first[i]) * (11 - i) for i in range(10))
            remainder2 = sum2 % 11
            digit2 = 0 if remainder2 < 2 else 11 - remainder2
            
            # Monta CPF completo
            full_cpf = base_digits + str(digit1) + str(digit2)
            
            # Verifica se não é padrão inválido
            if full_cpf in self.invalid_cpf_patterns:
                return None
            
            # Formata e retorna
            return f"{full_cpf[:3]}.{full_cpf[3:6]}.{full_cpf[6:9]}-{full_cpf[9:]}"
            
        except Exception:
            return None
    
    def _generate_document_suggestions(self) -> List[str]:
        """
        Gera sugestões padrão de documentos válidos.
        
        Returns:
            Lista de documentos de exemplo
        """
        if self.document_type == "cpf":
            return ["123.456.789-10", "987.654.321-00", "456.789.123-45"]
        elif self.document_type == "cep":
            return ["01234-567", "12345-678", "98765-432"]
        else:
            return [
                "123.456.789-10",  # CPF
                "01234-567",       # CEP
                "987.654.321-00"   # CPF
            ]