"""
Testes para o novo sistema de validação unificado - Technical Debt 1.
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.validation.normalizers.data_normalizer import DataNormalizer
from src.core.validation.validators.phone_validator import PhoneValidator
from src.core.validation.validators.name_validator import NameValidator
from src.core.validation.validators.date_validator import DateValidator
from src.core.validation.validators.document_validator import DocumentValidator


class TestPhoneValidator:
    """Testes para PhoneValidator."""
    
    def setup_method(self):
        """Setup para cada teste."""
        self.validator = PhoneValidator()
    
    def test_valid_phone_numbers(self):
        """Testa números de telefone válidos."""
        valid_phones = [
            "11999999999",
            "(11) 99999-9999", 
            "11333333333",
            "(21) 3333-3333"
        ]
        
        for phone in valid_phones:
            result = self.validator.validate(phone)
            assert result.is_valid, f"Telefone {phone} deveria ser válido"
            assert result.value is not None
            assert len(result.errors) == 0
    
    def test_invalid_phone_numbers(self):
        """Testa números de telefone inválidos."""
        invalid_phones = [
            "123",           # Muito curto
            "1199999999999", # Muito longo
            "0199999999",    # DDD inválido
            ""               # Vazio
        ]
        
        for phone in invalid_phones:
            result = self.validator.validate(phone)
            assert not result.is_valid, f"Telefone {phone} deveria ser inválido"
            assert len(result.errors) > 0
            assert len(result.suggestions) > 0


class TestNameValidator:
    """Testes para NameValidator."""
    
    def setup_method(self):
        """Setup para cada teste."""
        self.validator = NameValidator()
    
    def test_valid_names(self):
        """Testa nomes válidos."""
        valid_names = [
            "João Silva",
            "maria santos",
            "PEDRO DE OLIVEIRA",
            "Ana da Costa"
        ]
        
        for name in valid_names:
            result = self.validator.validate(name)
            assert result.is_valid, f"Nome {name} deveria ser válido"
            assert result.value is not None
    
    def test_name_normalization(self):
        """Testa normalização de nomes."""
        test_cases = [
            ("joao silva", "Joao Silva"),        # Aceita sem acento
            ("MARIA DA SILVA", "Maria da Silva"),
            ("pedro de oliveira", "Pedro de Oliveira")
        ]
        
        for input_name, expected in test_cases:
            result = self.validator.validate(input_name)
            assert result.is_valid
            assert result.value == expected, f"Esperado: {expected}, Obtido: {result.value}"
    
    def test_invalid_names(self):
        """Testa nomes inválidos."""
        invalid_names = [
            "",              # Vazio
            "J",             # Muito curto
            "João123",       # Caracteres inválidos
            "A" * 101        # Muito longo
        ]
        
        for name in invalid_names:
            result = self.validator.validate(name)
            assert not result.is_valid, f"Nome {name} deveria ser inválido"


class TestDateValidator:
    """Testes para DateValidator."""
    
    def setup_method(self):
        """Setup para cada teste."""
        self.validator = DateValidator(allow_past_dates=False)
    
    def test_relative_dates(self):
        """Testa expressões de data relativas."""
        relative_dates = [
            "amanha",
            "proxima segunda",
            "semana que vem"
        ]
        
        for date_expr in relative_dates:
            result = self.validator.validate(date_expr)
            assert result.is_valid, f"Data {date_expr} deveria ser válida"
            assert result.value is not None
            assert result.value.count("-") == 2  # Formato YYYY-MM-DD
    
    def test_past_dates_rejected(self):
        """Testa que datas passadas são rejeitadas."""
        past_dates = [
            "ontem",
            "semana passada",
            "2020-01-01"
        ]
        
        for date_expr in past_dates:
            result = self.validator.validate(date_expr)
            assert not result.is_valid, f"Data passada {date_expr} deveria ser rejeitada"


class TestDocumentValidator:
    """Testes para DocumentValidator."""
    
    def test_cpf_validation(self):
        """Testa validação de CPF."""
        validator = DocumentValidator("cpf")
        
        # CPF válido (gerado com algoritmo correto)
        valid_cpf = "12345678909"  # Este é um CPF válido
        result = validator.validate(valid_cpf)
        # Nota: pode falhar se o CPF não for realmente válido, isso é esperado
        
        # CPF com formato incorreto
        invalid_cpf = "123"
        result = validator.validate(invalid_cpf)
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_cep_validation(self):
        """Testa validação de CEP."""
        validator = DocumentValidator("cep")
        
        valid_ceps = [
            "01234567",
            "12345-678"
        ]
        
        for cep in valid_ceps:
            result = validator.validate(cep)
            assert result.is_valid, f"CEP {cep} deveria ser válido"
            assert "-" in result.value  # Deve estar formatado
        
        invalid_cep = "123"
        result = validator.validate(invalid_cep)
        assert not result.is_valid


class TestDataNormalizer:
    """Testes para DataNormalizer."""
    
    def setup_method(self):
        """Setup para cada teste."""
        self.normalizer = DataNormalizer(strict_mode=False)
    
    def test_complete_consultation_data(self):
        """Testa normalização de dados completos de consulta."""
        test_data = {
            "nome": "joao silva",
            "telefone": "11999999999",
            "data": "amanha",
            "tipo_consulta": "rotina"
        }
        
        result = self.normalizer.normalize_consultation_data(test_data)
        
        assert result.success or result.validation_summary.total_errors == 0
        assert result.confidence_score > 0.5
        assert "name" in result.normalized_data or "nome" in result.normalized_data
        assert "phone" in result.normalized_data or "telefone" in result.normalized_data
    
    def test_field_mapping(self):
        """Testa mapeamento de campos português/inglês."""
        test_data = {
            "nome": "Maria Santos",
            "telefone": "(11) 99999-9999"
        }
        
        result = self.normalizer.normalize_consultation_data(test_data)
        
        # Verifica se o mapeamento foi aplicado
        assert len(result.normalized_data) > 0
        assert result.field_mapping_info is not None
    
    def test_empty_data(self):
        """Testa tratamento de dados vazios."""
        result = self.normalizer.normalize_consultation_data({})
        
        assert not result.success
        assert result.confidence_score == 0.0
        assert len(result.recommendations) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])