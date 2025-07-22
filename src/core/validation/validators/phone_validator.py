"""
Validador especializado para números de telefone brasileiros.

Migrado de src/core/validators.py para eliminar duplicação de lógica.
Implementa validação, formatação e normalização de telefones brasileiros.
"""

import re
from typing import Any, List

from .base_validator import BaseValidator, ValidationResult


class PhoneValidator(BaseValidator):
    """
    Validador para números de telefone brasileiros.
    
    Suporta:
    - Telefones fixos: (11) 3333-3333
    - Telefones celulares: (11) 99999-9999
    - Validação de DDD brasileiro
    - Formatação automática
    - Sugestões de correção
    """
    
    def validate(self, value: Any, **kwargs) -> ValidationResult:
        """
        Valida número de telefone brasileiro.
        
        Args:
            value: Número de telefone a ser validado
            **kwargs: Parâmetros adicionais (não utilizados)
            
        Returns:
            ValidationResult com resultado da validação
        """
        if not value:
            return self._create_error_result(
                value,
                ["Telefone não pode ser vazio"],
                suggestions=["(11) 99999-9999", "(11) 3333-3333"]
            )
        
        try:
            # Converte para string e remove espaços
            phone_str = str(value).strip()
            
            # Remove todos os caracteres não numéricos
            digits_only = re.sub(r'\D', '', phone_str)
            
            # Valida número de dígitos
            if len(digits_only) not in [10, 11]:
                return self._create_error_result(
                    value,
                    ["Número deve ter 10 ou 11 dígitos (com DDD)"],
                    suggestions=self._generate_phone_suggestions()
                )
            
            # Valida DDD (deve estar entre 11 e 99)
            ddd = int(digits_only[:2])
            if ddd < 11 or ddd > 99:
                return self._create_error_result(
                    value,
                    ["DDD inválido (deve estar entre 11 e 99)"],
                    suggestions=self._generate_phone_suggestions()
                )
            
            # Formata o número
            formatted = self._format_phone(digits_only)
            
            # Determina tipo de telefone
            phone_type = "celular" if len(digits_only) == 11 else "fixo"
            
            # Valida primeiro dígito para celular
            warnings = []
            if len(digits_only) == 11 and digits_only[2] not in ['9', '8', '7', '6']:
                warnings.append("Primeiro dígito após DDD não é típico de celular")
            
            return self._create_success_result(
                original_value=value,
                normalized_value=formatted,
                warnings=warnings,
                confidence=0.9 if warnings else 1.0,
                metadata={
                    "phone_type": phone_type,
                    "ddd": ddd,
                    "digits_only": digits_only,
                    "is_mobile": len(digits_only) == 11
                }
            )
            
        except (ValueError, IndexError) as e:
            return self._create_error_result(
                value,
                [f"Erro no formato do telefone: {str(e)}"],
                suggestions=self._generate_phone_suggestions()
            )
        except Exception as e:
            return self._create_error_result(
                value,
                [f"Erro na validação: {str(e)}"],
                suggestions=self._generate_phone_suggestions()
            )
    
    def normalize(self, value: Any, **kwargs) -> str:
        """
        Normaliza número de telefone para formato padrão.
        
        Args:
            value: Número de telefone a ser normalizado
            **kwargs: Parâmetros adicionais (não utilizados)
            
        Returns:
            Telefone normalizado ou string vazia se inválido
        """
        result = self.validate(value, **kwargs)
        return result.value if result.is_valid else ""
    
    def suggest(self, value: Any, **kwargs) -> List[str]:
        """
        Gera sugestões de correção para telefone inválido.
        
        Args:
            value: Telefone que falhou na validação
            **kwargs: Parâmetros adicionais (não utilizados)
            
        Returns:
            Lista de sugestões de telefones válidos
        """
        if not value:
            return self._generate_phone_suggestions()
        
        try:
            phone_str = str(value).strip()
            digits_only = re.sub(r'\D', '', phone_str)
            
            suggestions = []
            
            # Se tem poucos dígitos, sugere completar
            if len(digits_only) < 8:
                suggestions.extend(self._generate_phone_suggestions())
            
            # Se tem dígitos demais, sugere remoção
            elif len(digits_only) > 11:
                # Tenta usar os últimos 11 ou 10 dígitos
                if len(digits_only) > 11:
                    shorter = digits_only[-11:]
                    if self.validate(shorter).is_valid:
                        suggestions.append(self._format_phone(shorter))
                
                shorter = digits_only[-10:]
                if self.validate(shorter).is_valid:
                    suggestions.append(self._format_phone(shorter))
            
            # Se DDD inválido, sugere DDDs válidos
            elif len(digits_only) in [10, 11]:
                try:
                    ddd = int(digits_only[:2])
                    if ddd < 11 or ddd > 99:
                        valid_ddds = ["11", "21", "31", "41", "51", "61", "71", "81", "85", "91"]
                        for valid_ddd in valid_ddds[:3]:
                            suggested_digits = valid_ddd + digits_only[2:]
                            suggestions.append(self._format_phone(suggested_digits))
                except ValueError:
                    suggestions.extend(self._generate_phone_suggestions())
            
            if not suggestions:
                suggestions = self._generate_phone_suggestions()
                
            return suggestions[:5]  # Limita a 5 sugestões
            
        except Exception:
            return self._generate_phone_suggestions()
    
    def get_validation_rules(self) -> dict:
        """
        Retorna regras de validação aplicadas.
        
        Returns:
            Dicionário com regras de validação
        """
        return {
            "min_digits": 10,
            "max_digits": 11,
            "ddd_range": {"min": 11, "max": 99},
            "mobile_digits": 11,
            "landline_digits": 10,
            "format_mobile": "(XX) 9XXXX-XXXX",
            "format_landline": "(XX) XXXX-XXXX",
            "country": "Brazil"
        }
    
    def _format_phone(self, digits_only: str) -> str:
        """
        Formata número de telefone limpo.
        
        Args:
            digits_only: String com apenas dígitos
            
        Returns:
            Telefone formatado
        """
        if len(digits_only) == 11:
            # Celular: (11) 99999-9999
            return f"({digits_only[:2]}) {digits_only[2:7]}-{digits_only[7:]}"
        elif len(digits_only) == 10:
            # Fixo: (11) 3333-3333
            return f"({digits_only[:2]}) {digits_only[2:6]}-{digits_only[6:]}"
        else:
            return digits_only
    
    def _generate_phone_suggestions(self) -> List[str]:
        """
        Gera sugestões padrão de telefones válidos.
        
        Returns:
            Lista de telefones de exemplo
        """
        return [
            "(11) 99999-9999",  # Celular SP
            "(11) 3333-3333",   # Fixo SP
            "(21) 99999-9999",  # Celular RJ
            "(21) 3333-3333",   # Fixo RJ
            "(85) 99999-9999"   # Celular CE
        ]