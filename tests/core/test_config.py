import pytest
import os
from unittest.mock import patch, MagicMock
from src.core.config import Settings, SettingsManager, get_settings


class TestSettings:
    """Testes para a classe Settings."""

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
    })
    def test_settings_initialization_with_required_vars(self):
        """Testa inicialização com variáveis obrigatórias."""
        settings = Settings()
        
        assert settings.DATABASE_URL == "postgresql://user:pass@localhost:5432/test"
        assert settings.OPENAI_API_KEY == "test-key-123"
        assert settings.OPENAI_MODEL == "gpt-4o-mini"  # valor padrão
        assert settings.OPENAI_MAX_TOKENS == 500  # valor padrão
        assert settings.LOG_LEVEL == "INFO"  # valor padrão
        assert settings.APP_NAME == "Data Structuring Agent"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "OPENAI_MODEL": "gpt-4-turbo",
        "OPENAI_MAX_TOKENS": "1000",
        "LOG_LEVEL": "DEBUG",
        "DEBUG": "true",
        "HOST": "127.0.0.1",
        "PORT": "3000"
    })
    def test_settings_initialization_with_custom_values(self):
        """Testa inicialização com valores customizados."""
        settings = Settings()
        
        assert settings.OPENAI_MODEL == "gpt-4-turbo"
        assert settings.OPENAI_MAX_TOKENS == 1000
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.DEBUG is True
        assert settings.HOST == "127.0.0.1"
        assert settings.PORT == 3000

    def test_missing_database_url_raises_error(self):
        """Testa erro quando DATABASE_URL está ausente."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="DATABASE_URL is required"):
                Settings()

    def test_missing_openai_api_key_raises_error(self):
        """Testa erro quando OPENAI_API_KEY está ausente."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://user:pass@localhost:5432/test"
        }, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
                Settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "invalid://url",
        "OPENAI_API_KEY": "test-key-123",
    })
    def test_invalid_database_url_raises_error(self):
        """Testa erro com DATABASE_URL inválida."""
        with pytest.raises(ValueError, match="DATABASE_URL must be a valid PostgreSQL"):
            Settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "LOG_LEVEL": "INVALID"
    })
    def test_invalid_log_level_raises_error(self):
        """Testa erro com LOG_LEVEL inválido."""
        with pytest.raises(ValueError, match="LOG_LEVEL must be one of"):
            Settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "PORT": "99999"
    })
    def test_invalid_port_raises_error(self):
        """Testa erro com porta inválida."""
        with pytest.raises(ValueError, match="PORT must be between 1 and 65535"):
            Settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "OPENAI_TIMEOUT": "500"
    })
    def test_invalid_openai_timeout_raises_error(self):
        """Testa erro com timeout OpenAI inválido."""
        with pytest.raises(ValueError, match="OPENAI_TIMEOUT must be between 1 and 300"):
            Settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "ALLOWED_ORIGINS": "http://localhost:3000,https://example.com,invalid-origin"
    })
    def test_invalid_cors_origin_raises_error(self):
        """Testa erro com origem CORS inválida."""
        with pytest.raises(ValueError, match="Invalid CORS origin format"):
            Settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "ALLOWED_ORIGINS": "http://localhost:3000,https://example.com"
    })
    def test_cors_origins_parsing(self):
        """Testa parsing de origens CORS."""
        settings = Settings()
        
        assert "http://localhost:3000" in settings.ALLOWED_ORIGINS
        assert "https://example.com" in settings.ALLOWED_ORIGINS
        assert len(settings.ALLOWED_ORIGINS) == 2

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123"
    })
    def test_default_cors_origins(self):
        """Testa origens CORS padrão."""
        settings = Settings()
        
        assert "http://localhost:3000" in settings.ALLOWED_ORIGINS
        assert "http://localhost:5678" in settings.ALLOWED_ORIGINS
        assert "http://localhost:8000" in settings.ALLOWED_ORIGINS
        assert "http://localhost:3001" in settings.ALLOWED_ORIGINS

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "MESSAGE_MIN_LENGTH": "5",
        "MESSAGE_MAX_LENGTH": "1000",
        "NAME_MIN_LENGTH": "3",
        "NAME_MAX_LENGTH": "50"
    })
    def test_schema_validation_limits(self):
        """Testa limites de validação de schema."""
        settings = Settings()
        
        assert settings.MESSAGE_MIN_LENGTH == 5
        assert settings.MESSAGE_MAX_LENGTH == 1000
        assert settings.NAME_MIN_LENGTH == 3
        assert settings.NAME_MAX_LENGTH == 50

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "MESSAGE_MIN_LENGTH": "100",
        "MESSAGE_MAX_LENGTH": "50"
    })
    def test_invalid_schema_limits_raises_error(self):
        """Testa erro com limites de schema inválidos."""
        with pytest.raises(ValueError, match="MESSAGE_MIN_LENGTH must be between"):
            Settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "OPENAI_API_URL": "invalid-url"
    })
    def test_invalid_api_url_raises_error(self):
        """Testa erro com URL da API inválida."""
        with pytest.raises(ValueError, match="OPENAI_API_URL must start with"):
            Settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "HOST": "localhost",
        "PORT": "3000"
    })
    def test_base_url_construction(self):
        """Testa construção da BASE_URL."""
        settings = Settings()
        
        assert settings.BASE_URL == "http://localhost:3000"


class TestSettingsManager:
    """Testes para o gerenciador singleton de Settings."""

    def setup_method(self):
        """Reset o singleton antes de cada teste."""
        SettingsManager.reset_settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123"
    })
    def test_singleton_behavior(self):
        """Testa comportamento de singleton."""
        settings1 = SettingsManager.get_settings()
        settings2 = SettingsManager.get_settings()
        
        assert settings1 is settings2
        assert id(settings1) == id(settings2)

    def test_configuration_error_handling(self):
        """Testa tratamento de erro de configuração."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Configuration error"):
                SettingsManager.get_settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123"
    })
    def test_reset_settings(self):
        """Testa reset do singleton."""
        settings1 = SettingsManager.get_settings()
        
        SettingsManager.reset_settings()
        
        settings2 = SettingsManager.get_settings()
        
        assert settings1 is not settings2


class TestGetSettingsFunction:
    """Testes para a função convenience get_settings."""

    def setup_method(self):
        """Reset o singleton antes de cada teste."""
        SettingsManager.reset_settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123"
    })
    def test_get_settings_function(self):
        """Testa função get_settings."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
        assert isinstance(settings1, Settings)

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123"
    })
    def test_get_settings_consistency_with_manager(self):
        """Testa consistência entre get_settings e SettingsManager."""
        settings_from_function = get_settings()
        settings_from_manager = SettingsManager.get_settings()
        
        assert settings_from_function is settings_from_manager


class TestSettingsValidation:
    """Testes para validações específicas de Settings."""

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "DB_CONNECTION_TIMEOUT": "0.05"
    })
    def test_invalid_db_timeout_raises_error(self):
        """Testa erro com timeout de DB inválido."""
        with pytest.raises(ValueError, match="DB_CONNECTION_TIMEOUT must be between"):
            Settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "MAX_API_RETRIES": "15"
    })
    def test_invalid_max_retries_raises_error(self):
        """Testa erro com número máximo de tentativas inválido."""
        with pytest.raises(ValueError, match="MAX_API_RETRIES must be between"):
            Settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "MESSAGE_MAX_LENGTH": "15000"
    })
    def test_invalid_message_max_length_raises_error(self):
        """Testa erro com comprimento máximo de mensagem inválido."""
        with pytest.raises(ValueError, match="MESSAGE_MAX_LENGTH must be <= 10000"):
            Settings()

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgres://user:pass@localhost:5432/test",  # postgres:// também é válido
        "OPENAI_API_KEY": "test-key-123"
    })
    def test_postgres_url_scheme_valid(self):
        """Testa que scheme postgres:// também é válido."""
        settings = Settings()
        
        assert settings.DATABASE_URL == "postgres://user:pass@localhost:5432/test"

    @patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "OPENAI_API_KEY": "test-key-123",
        "OPENAI_API_URL": "https://custom-api.example.com/v1/chat/completions"
    })
    def test_custom_openai_api_url(self):
        """Testa URL customizada da API OpenAI."""
        settings = Settings()
        
        assert settings.OPENAI_API_URL == "https://custom-api.example.com/v1/chat/completions"