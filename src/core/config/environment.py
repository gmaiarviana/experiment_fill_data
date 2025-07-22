"""
Environment detection and configuration for the Data Structuring Agent.

This module provides utilities to detect the current environment (dev, test, prod)
and apply environment-specific configurations.
"""

import os
from enum import Enum
from typing import Dict, Any


class Environment(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class EnvironmentDetector:
    """
    Detects the current environment and provides environment-specific configurations.
    """
    
    @staticmethod
    def get_environment() -> Environment:
        """
        Detect the current environment based on environment variables.
        
        Returns:
            Environment: The detected environment
        """
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        
        # Handle common environment variable names
        if not env_name or env_name in ["dev", "development"]:
            return Environment.DEVELOPMENT
        elif env_name in ["test", "testing"]:
            return Environment.TESTING
        elif env_name in ["prod", "production"]:
            return Environment.PRODUCTION
        else:
            # Default to development for unknown environments
            return Environment.DEVELOPMENT
    
    @staticmethod
    def is_development() -> bool:
        """Check if running in development environment."""
        return EnvironmentDetector.get_environment() == Environment.DEVELOPMENT
    
    @staticmethod
    def is_testing() -> bool:
        """Check if running in testing environment."""
        return EnvironmentDetector.get_environment() == Environment.TESTING
    
    @staticmethod
    def is_production() -> bool:
        """Check if running in production environment."""
        return EnvironmentDetector.get_environment() == Environment.PRODUCTION
    
    @staticmethod
    def get_environment_config() -> Dict[str, Any]:
        """
        Get environment-specific configuration overrides.
        
        Returns:
            Dict[str, Any]: Environment-specific settings
        """
        env = EnvironmentDetector.get_environment()
        
        if env == Environment.DEVELOPMENT:
            return {
                "debug": True,
                "log_level": "DEBUG",
                "openai_timeout": 30,
                "db_connection_timeout": 5.0,
                "allowed_origins": [
                    "http://localhost:3000",
                    "http://localhost:5678", 
                    "http://localhost:8000",
                    "http://localhost:3001",
                ]
            }
        
        elif env == Environment.TESTING:
            return {
                "debug": False,
                "log_level": "WARNING",
                "openai_timeout": 10,
                "db_connection_timeout": 2.0,
                "allowed_origins": ["http://localhost:3000"]
            }
        
        elif env == Environment.PRODUCTION:
            return {
                "debug": False,
                "log_level": "INFO",
                "openai_timeout": 60,
                "db_connection_timeout": 10.0,
                "allowed_origins": []  # Must be explicitly configured
            }
        
        return {}


# Convenience functions
def get_current_environment() -> Environment:
    """Get the current environment."""
    return EnvironmentDetector.get_environment()


def get_environment_name() -> str:
    """Get the current environment name as string."""
    return EnvironmentDetector.get_environment().value


def is_development() -> bool:
    """Check if running in development."""
    return EnvironmentDetector.is_development()


def is_testing() -> bool:
    """Check if running in testing."""
    return EnvironmentDetector.is_testing()


def is_production() -> bool:
    """Check if running in production."""
    return EnvironmentDetector.is_production()