"""
Validador especializado para nomes próprios em português brasileiro.

Migrado de src/core/validators.py para eliminar duplicação de lógica.
Implementa normalização com capitalização adequada e validação
de nomes completos respeitando preposições e artigos.
"""

from typing import Any, List

from .base_validator import BaseValidator, ValidationResult


class NameValidator(BaseValidator):
    """
    Validador para nomes próprios em português brasileiro.
    
    Suporta:
    - Capitalização automática respeitando preposições
    - Validação de nomes completos (nome + sobrenome)
    - Normalização de espaços extras
    - Tratamento de artigos e preposições em minúsculo
    - Validação de caracteres especiais
    """
    
    def __init__(self, require_full_name: bool = True, min_words: int = 2):
        """
        Inicializa o validador de nomes.
        
        Args:
            require_full_name: Se True, exige pelo menos nome e sobrenome
            min_words: Número mínimo de palavras no nome
        """
        self.require_full_name = require_full_name
        self.min_words = min_words
        
        # Preposições e artigos que devem ficar em minúsculo
        self.lowercase_words = {
            'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'nas', 'nos',
            'para', 'por', 'com', 'sem', 'sob', 'sobre', 'entre', 'contra',
            'desde', 'até', 'ante', 'após', 'perante', 'segundo',
            'conforme', 'mediante', 'salvo', 'exceto', 'menos', 'fora'
        }
    
    def validate(self, value: Any, **kwargs) -> ValidationResult:
        """
        Valida nome próprio em português.
        
        Args:
            value: Nome a ser validado
            **kwargs: Parâmetros adicionais
                     - require_full_name: sobrescreve require_full_name
                     - min_words: sobrescreve min_words
                     
        Returns:
            ValidationResult com resultado da validação
        """
        if not value:
            return self._create_error_result(
                value,
                ["Nome não pode ser vazio"],
                suggestions=["João Silva", "Maria Santos", "Carlos Oliveira"]
            )
        
        try:
            name_str = str(value).strip()
            
            # Valida caracteres inválidos
            if not self._has_valid_characters(name_str):
                return self._create_error_result(
                    value,
                    ["Nome contém caracteres inválidos"],
                    suggestions=["Use apenas letras, espaços, acentos e hífens"]
                )
            
            # Valida comprimento
            if len(name_str) < 2:
                return self._create_error_result(
                    value,
                    ["Nome muito curto (mínimo 2 caracteres)"],
                    suggestions=["João Silva", "Ana Costa", "Pedro Santos"]
                )
            
            if len(name_str) > 100:
                return self._create_error_result(
                    value,
                    ["Nome muito longo (máximo 100 caracteres)"],
                    suggestions=["Considere usar apenas nome e sobrenome principal"]
                )
            
            # Remove espaços extras e divide em palavras
            words = name_str.split()
            words = [word for word in words if word]  # Remove strings vazias
            
            # Valida número de palavras
            require_full = kwargs.get("require_full_name", self.require_full_name)
            min_words = kwargs.get("min_words", self.min_words)
            
            if len(words) < min_words:
                error_msg = f"Nome deve ter pelo menos {min_words} palavra"
                error_msg += "s" if min_words > 1 else ""
                if require_full:
                    error_msg += " (nome e sobrenome)"
                    
                return self._create_error_result(
                    value,
                    [error_msg],
                    suggestions=["João Silva", "Maria Santos", "Ana Costa"]
                )
            
            # Normaliza o nome
            normalized_name = self._normalize_name_words(words)
            
            # Validações adicionais
            warnings = []
            confidence = 1.0
            
            # Verifica palavras muito curtas (exceto preposições conhecidas)
            short_words = [
                word for word in words 
                if len(word) < 2 and word.lower() not in self.lowercase_words
            ]
            if short_words:
                warnings.append(f"Palavras muito curtas: {', '.join(short_words)}")
                confidence = 0.8
            
            # Verifica se tem apenas uma palavra mas está configurado para aceitar
            if len(words) == 1 and require_full:
                warnings.append("Nome pode estar incompleto (sem sobrenome)")
                confidence = 0.7
            
            return self._create_success_result(
                original_value=value,
                normalized_value=normalized_name,
                warnings=warnings,
                confidence=confidence,
                metadata={
                    "word_count": len(words),
                    "has_prepositions": any(
                        word.lower() in self.lowercase_words for word in words
                    ),
                    "original_words": words,
                    "normalized_words": normalized_name.split()
                }
            )
            
        except Exception as e:
            return self._create_error_result(
                value,
                [f"Erro na validação: {str(e)}"],
                suggestions=["João Silva", "Maria Santos", "Pedro Costa"]
            )
    
    def normalize(self, value: Any, **kwargs) -> str:
        """
        Normaliza nome para formato adequado.
        
        Args:
            value: Nome a ser normalizado
            **kwargs: Parâmetros adicionais
            
        Returns:
            Nome normalizado ou string vazia se inválido
        """
        result = self.validate(value, **kwargs)
        return result.value if result.is_valid else ""
    
    def suggest(self, value: Any, **kwargs) -> List[str]:
        """
        Gera sugestões de nomes válidos.
        
        Args:
            value: Nome que falhou na validação
            **kwargs: Parâmetros adicionais
            
        Returns:
            Lista de sugestões de nomes
        """
        if not value:
            return self._generate_name_suggestions()
        
        try:
            name_str = str(value).strip()
            words = name_str.split()
            
            suggestions = []
            
            # Se tem uma palavra, sugere sobrenomes
            if len(words) == 1 and self._has_valid_characters(name_str):
                first_name = words[0].capitalize()
                common_surnames = ["Silva", "Santos", "Oliveira", "Costa", "Pereira"]
                for surname in common_surnames[:3]:
                    suggestions.append(f"{first_name} {surname}")
            
            # Se tem palavras com problemas, tenta corrigir
            elif len(words) >= 2:
                try:
                    normalized = self._normalize_name_words(words)
                    if normalized != name_str:
                        suggestions.append(normalized)
                except:
                    pass
            
            # Adiciona sugestões padrão
            if not suggestions or len(suggestions) < 3:
                suggestions.extend(self._generate_name_suggestions())
            
            return suggestions[:5]  # Limita a 5 sugestões
            
        except Exception:
            return self._generate_name_suggestions()
    
    def get_validation_rules(self) -> dict:
        """
        Retorna regras de validação aplicadas.
        
        Returns:
            Dicionário com regras de validação
        """
        return {
            "require_full_name": self.require_full_name,
            "min_words": self.min_words,
            "max_length": 100,
            "min_length": 2,
            "allowed_characters": "letras, espaços, acentos, hífens, apostrofes",
            "lowercase_prepositions": sorted(list(self.lowercase_words)),
            "capitalization": "primeira_letra_cada_palavra_exceto_preposições"
        }
    
    def _normalize_name_words(self, words: List[str]) -> str:
        """
        Normaliza lista de palavras do nome.
        
        Args:
            words: Lista de palavras do nome
            
        Returns:
            Nome normalizado como string
        """
        normalized_words = []
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            
            # Primeira palavra sempre capitalizada
            if i == 0:
                normalized_words.append(word.capitalize())
            # Última palavra sempre capitalizada  
            elif i == len(words) - 1:
                normalized_words.append(word.capitalize())
            # Palavras do meio: capitaliza se não for preposição/artigo
            elif word_lower not in self.lowercase_words:
                normalized_words.append(word.capitalize())
            else:
                normalized_words.append(word_lower)
        
        return " ".join(normalized_words)
    
    def _has_valid_characters(self, name_str: str) -> bool:
        """
        Verifica se o nome contém apenas caracteres válidos.
        
        Args:
            name_str: String do nome
            
        Returns:
            True se todos os caracteres são válidos
        """
        import unicodedata
        import re
        
        # Padrão para caracteres válidos em nomes
        # Permite: letras (incluindo acentuadas), espaços, hífens, apostrofes
        valid_pattern = r"^[a-zA-ZÀ-ÿ\s\-'\.]+$"
        
        return bool(re.match(valid_pattern, name_str))
    
    def _generate_name_suggestions(self) -> List[str]:
        """
        Gera sugestões padrão de nomes válidos.
        
        Returns:
            Lista de nomes de exemplo
        """
        return [
            "João Silva",
            "Maria Santos", 
            "Pedro Oliveira",
            "Ana Costa",
            "Carlos Pereira",
            "Luiza Almeida"
        ]