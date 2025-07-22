"""
Extended settings for the Data Structuring Agent.

This module extends the base configuration with additional settings
for timeouts, CORS, API URLs and other distributed configurations.
"""

import os
from typing import List, Dict, Any
from .validation import validate_config

# Import base settings directly to avoid circular import
import sys
import importlib.util
base_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.py")
spec = importlib.util.spec_from_file_location("base_config", base_config_path)
base_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_config)
BaseSettings = base_config.Settings


class ExtendedSettings(BaseSettings):
    """
    Extended settings class that adds configurations for timeouts, CORS, API URLs
    and other distributed settings found throughout the codebase.
    """
    
    def __init__(self):
        super().__init__()
        
        # API Configuration
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
        
        # Validate extended fields
        self._validate_timeouts()
        self._validate_schema_limits()
        
        # Comprehensive validation using validation module
        self._validate_all_config()
    
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
    
    def _validate_timeouts(self):
        """Validate that timeout values are reasonable."""
        if not 1 <= self.OPENAI_TIMEOUT <= 300:
            raise ValueError("OPENAI_TIMEOUT must be between 1 and 300 seconds")
        
        if not 0.1 <= self.DB_CONNECTION_TIMEOUT <= 60.0:
            raise ValueError("DB_CONNECTION_TIMEOUT must be between 0.1 and 60.0 seconds")
        
        if not 1 <= self.API_REQUEST_TIMEOUT <= 120:
            raise ValueError("API_REQUEST_TIMEOUT must be between 1 and 120 seconds")
        
        if not 1 <= self.MAX_API_RETRIES <= 10:
            raise ValueError("MAX_API_RETRIES must be between 1 and 10")
    
    def _validate_schema_limits(self):
        """Validate schema field limits are reasonable."""
        if not 1 <= self.MESSAGE_MIN_LENGTH <= self.MESSAGE_MAX_LENGTH:
            raise ValueError("MESSAGE_MIN_LENGTH must be between 1 and MESSAGE_MAX_LENGTH")
        
        if not self.MESSAGE_MAX_LENGTH <= 10000:
            raise ValueError("MESSAGE_MAX_LENGTH must be <= 10000")
        
        if not 1 <= self.NAME_MIN_LENGTH <= self.NAME_MAX_LENGTH:
            raise ValueError("NAME_MIN_LENGTH must be between 1 and NAME_MAX_LENGTH")
        
        if not self.NAME_MAX_LENGTH <= 500:
            raise ValueError("NAME_MAX_LENGTH must be <= 500")
    
    def _validate_all_config(self):
        """Validate all configuration using the validation module."""
        config_dict = {
            "DATABASE_URL": self.DATABASE_URL,
            "OPENAI_API_KEY": self.OPENAI_API_KEY,
            "PORT": self.PORT,
            "LOG_LEVEL": self.LOG_LEVEL,
            "OPENAI_TIMEOUT": self.OPENAI_TIMEOUT,
            "DB_CONNECTION_TIMEOUT": self.DB_CONNECTION_TIMEOUT,
            "API_REQUEST_TIMEOUT": self.API_REQUEST_TIMEOUT,
            "ALLOWED_ORIGINS": self.ALLOWED_ORIGINS,
            "OPENAI_API_URL": self.OPENAI_API_URL,
        }
        
        errors = validate_config(config_dict)
        if errors:
            error_messages = [f"{key}: {value}" for key, value in errors.items()]
            raise ValueError(f"Configuration validation errors: {'; '.join(error_messages)}")


# Create singleton instance
_extended_settings = None

def get_extended_settings() -> ExtendedSettings:
    """
    Get the extended settings singleton instance.
    
    Returns:
        ExtendedSettings: The extended application settings
    """
    global _extended_settings
    if _extended_settings is None:
        _extended_settings = ExtendedSettings()
    return _extended_settings


# Export for easy access
extended_settings = get_extended_settings()