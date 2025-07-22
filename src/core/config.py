"""
Centralized configuration management for the Data Structuring Agent.

This module provides a Settings class that manages all environment variables
with validation and clear error messages.
"""

import os
from typing import Optional, List


class Settings:
    """
    Centralized settings class for the application.
    
    Loads configuration from environment variables with validation.
    """
    
    def __init__(self):
        # Database Configuration
        self.DATABASE_URL = self._get_required_env("DATABASE_URL")
        
        # OpenAI Configuration
        self.OPENAI_API_KEY = self._get_required_env("OPENAI_API_KEY")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Application Configuration
        self.APP_NAME = "Data Structuring Agent"
        self.APP_VERSION = "1.0.0"
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        
        # Server Configuration
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8000"))
        
        # Extended API Configuration
        self.OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
        self.OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))
        
        # Database Timeouts
        self.DB_CONNECTION_TIMEOUT = float(os.getenv("DB_CONNECTION_TIMEOUT", "5.0"))
        
        # API Request Timeouts
        self.API_REQUEST_TIMEOUT = int(os.getenv("API_REQUEST_TIMEOUT", "10"))
        self.MAX_API_RETRIES = int(os.getenv("MAX_API_RETRIES", "3"))
        
        # CORS Configuration
        self.ALLOWED_ORIGINS = self._parse_cors_origins()
        
        # Schema Validation Limits
        self.MESSAGE_MIN_LENGTH = int(os.getenv("MESSAGE_MIN_LENGTH", "1"))
        self.MESSAGE_MAX_LENGTH = int(os.getenv("MESSAGE_MAX_LENGTH", "2000"))
        self.NAME_MIN_LENGTH = int(os.getenv("NAME_MIN_LENGTH", "2"))
        self.NAME_MAX_LENGTH = int(os.getenv("NAME_MAX_LENGTH", "100"))
        
        # Application URLs
        self.BASE_URL = f"http://{self.HOST}:{self.PORT}"
        
        # Validate fields
        self._validate_database_url()
        self._validate_log_level()
        self._validate_port()
        self._validate_extended_settings()
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise clear error."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"{key} is required but not set in environment variables")
        return value
    
    def _validate_database_url(self):
        """Validate that DATABASE_URL has correct format."""
        if not self.DATABASE_URL.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL connection string")
    
    def _validate_log_level(self):
        """Validate log level is one of the allowed values."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.LOG_LEVEL not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(allowed_levels)}")
    
    def _validate_port(self):
        """Validate port is within valid range."""
        if not 1 <= self.PORT <= 65535:
            raise ValueError("PORT must be between 1 and 65535")
    
    def _parse_cors_origins(self) -> List[str]:
        """Parse CORS origins from environment variable or use defaults."""
        cors_env = os.getenv("ALLOWED_ORIGINS")
        if cors_env:
            # Parse comma-separated origins
            return [origin.strip() for origin in cors_env.split(",")]
        
        # Default origins for development
        return [
            "http://localhost:3000",
            "http://localhost:5678", 
            "http://localhost:8000",
            "http://localhost:3001",
        ]
    
    def _validate_extended_settings(self):
        """Validate extended configuration settings."""
        # Validate timeouts
        if not 1 <= self.OPENAI_TIMEOUT <= 300:
            raise ValueError("OPENAI_TIMEOUT must be between 1 and 300 seconds")
        
        if not 0.1 <= self.DB_CONNECTION_TIMEOUT <= 60.0:
            raise ValueError("DB_CONNECTION_TIMEOUT must be between 0.1 and 60.0 seconds")
        
        if not 1 <= self.API_REQUEST_TIMEOUT <= 120:
            raise ValueError("API_REQUEST_TIMEOUT must be between 1 and 120 seconds")
        
        if not 1 <= self.MAX_API_RETRIES <= 10:
            raise ValueError("MAX_API_RETRIES must be between 1 and 10")
        
        # Validate schema limits
        if not 1 <= self.MESSAGE_MIN_LENGTH <= self.MESSAGE_MAX_LENGTH:
            raise ValueError("MESSAGE_MIN_LENGTH must be between 1 and MESSAGE_MAX_LENGTH")
        
        if not self.MESSAGE_MAX_LENGTH <= 10000:
            raise ValueError("MESSAGE_MAX_LENGTH must be <= 10000")
        
        if not 1 <= self.NAME_MIN_LENGTH <= self.NAME_MAX_LENGTH:
            raise ValueError("NAME_MIN_LENGTH must be between 1 and NAME_MAX_LENGTH")
        
        if not self.NAME_MAX_LENGTH <= 500:
            raise ValueError("NAME_MAX_LENGTH must be <= 500")
        
        # Validate API URL
        if not self.OPENAI_API_URL.startswith(("http://", "https://")):
            raise ValueError("OPENAI_API_URL must start with 'http://' or 'https://'")
        
        # Validate CORS origins format
        for origin in self.ALLOWED_ORIGINS:
            if origin and not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid CORS origin format: {origin}")


class SettingsManager:
    """
    Singleton manager for Settings to ensure single instance across application.
    """
    _instance: Optional[Settings] = None
    
    @classmethod
    def get_settings(cls) -> Settings:
        """
        Get or create the singleton Settings instance.
        
        Returns:
            Settings: The application settings instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        if cls._instance is None:
            try:
                cls._instance = Settings()
            except ValueError as e:
                # Provide clear error message for missing required variables
                raise ValueError(
                    f"Configuration error: {str(e)}. "
                    "Please check your environment variables or .env file."
                ) from e
        return cls._instance
    
    @classmethod
    def reset_settings(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None


# Convenience function to get settings
def get_settings() -> Settings:
    """
    Get the application settings.
    
    Returns:
        Settings: The application settings instance
    """
    return SettingsManager.get_settings()


# Export the main settings instance for easy access
settings = get_settings()