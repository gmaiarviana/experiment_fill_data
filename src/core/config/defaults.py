"""
Default configuration values for the Data Structuring Agent.

This module centralizes all default values used throughout the application,
making them easy to maintain and override.
"""

from typing import Dict, Any, List


class DefaultConfig:
    """
    Container for all default configuration values.
    """
    
    # Application Information
    APP_NAME = "Data Structuring Agent"
    APP_VERSION = "1.0.0"
    
    # Server Defaults
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = False
    
    # OpenAI Defaults
    OPENAI_MODEL = "gpt-4o-mini"
    OPENAI_MAX_TOKENS = 500
    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
    OPENAI_TIMEOUT = 30
    
    # Database Defaults
    DB_CONNECTION_TIMEOUT = 5.0
    
    # API Defaults
    API_REQUEST_TIMEOUT = 10
    MAX_API_RETRIES = 3
    
    # Logging Defaults
    LOG_LEVEL = "INFO"
    
    # CORS Defaults (Development)
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5678",
        "http://localhost:8000",
        "http://localhost:3001",
    ]
    
    # Schema Validation Defaults
    MESSAGE_MIN_LENGTH = 1
    MESSAGE_MAX_LENGTH = 2000
    NAME_MIN_LENGTH = 2
    NAME_MAX_LENGTH = 100
    
    # Environment Defaults
    ENVIRONMENT = "development"


class ProductionDefaults(DefaultConfig):
    """
    Production-specific default values.
    """
    
    DEBUG = False
    LOG_LEVEL = "INFO"
    OPENAI_TIMEOUT = 60
    DB_CONNECTION_TIMEOUT = 10.0
    API_REQUEST_TIMEOUT = 20
    ALLOWED_ORIGINS = []  # Must be explicitly configured in production


class TestingDefaults(DefaultConfig):
    """
    Testing-specific default values.
    """
    
    DEBUG = False
    LOG_LEVEL = "WARNING"
    OPENAI_TIMEOUT = 10
    DB_CONNECTION_TIMEOUT = 2.0
    API_REQUEST_TIMEOUT = 5
    MAX_API_RETRIES = 1
    ALLOWED_ORIGINS = ["http://localhost:3000"]


def get_defaults_for_environment(environment: str) -> Dict[str, Any]:
    """
    Get default values for a specific environment.
    
    Args:
        environment: The environment name (development, testing, production)
        
    Returns:
        Dict[str, Any]: Default configuration values
    """
    env = environment.lower()
    
    if env in ["production", "prod"]:
        defaults_class = ProductionDefaults
    elif env in ["testing", "test"]:
        defaults_class = TestingDefaults
    else:
        defaults_class = DefaultConfig
    
    # Convert class attributes to dictionary
    return {
        key: value for key, value in defaults_class.__dict__.items()
        if not key.startswith('_') and not callable(value)
    }


def get_development_defaults() -> Dict[str, Any]:
    """Get development environment defaults."""
    return get_defaults_for_environment("development")


def get_production_defaults() -> Dict[str, Any]:
    """Get production environment defaults."""
    return get_defaults_for_environment("production")


def get_testing_defaults() -> Dict[str, Any]:
    """Get testing environment defaults."""
    return get_defaults_for_environment("testing")


# Standard defaults (development)
DEFAULTS = get_development_defaults()