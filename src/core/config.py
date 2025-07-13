"""
Centralized configuration management for the Data Structuring Agent.

This module provides a Settings class that manages all environment variables
with validation and clear error messages.
"""

import os
from typing import Optional


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
        
        # Validate fields
        self._validate_database_url()
        self._validate_log_level()
        self._validate_port()
    
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