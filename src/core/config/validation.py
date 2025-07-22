"""
Configuration validation utilities for the Data Structuring Agent.

This module provides comprehensive validation for all configuration values
with clear error messages and type checking.
"""

import re
import urllib.parse
from typing import List, Any, Dict, Union


class ConfigValidator:
    """
    Validator for application configuration with comprehensive checks.
    """
    
    @staticmethod
    def validate_database_url(url: str) -> bool:
        """
        Validate PostgreSQL database URL format.
        
        Args:
            url: The database URL to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If URL is invalid
        """
        if not url:
            raise ValueError("Database URL cannot be empty")
        
        if not url.startswith(("postgresql://", "postgres://")):
            raise ValueError("Database URL must start with 'postgresql://' or 'postgres://'")
        
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.hostname:
                raise ValueError("Database URL must include hostname")
            if not parsed.path or parsed.path == "/":
                raise ValueError("Database URL must include database name")
        except Exception as e:
            raise ValueError(f"Invalid database URL format: {e}")
        
        return True
    
    @staticmethod
    def validate_openai_api_key(api_key: str) -> bool:
        """
        Validate OpenAI API key format.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If API key is invalid
        """
        if not api_key:
            raise ValueError("OpenAI API key cannot be empty")
        
        if not api_key.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        
        if len(api_key) < 20:
            raise ValueError("OpenAI API key appears to be too short")
        
        return True
    
    @staticmethod
    def validate_port(port: int) -> bool:
        """
        Validate port number.
        
        Args:
            port: The port number to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If port is invalid
        """
        if not isinstance(port, int):
            raise ValueError("Port must be an integer")
        
        if not 1 <= port <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        
        return True
    
    @staticmethod
    def validate_timeout(timeout: Union[int, float], min_val: float = 0.1, max_val: float = 300.0) -> bool:
        """
        Validate timeout value.
        
        Args:
            timeout: The timeout value to validate
            min_val: Minimum allowed timeout
            max_val: Maximum allowed timeout
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If timeout is invalid
        """
        if not isinstance(timeout, (int, float)):
            raise ValueError("Timeout must be a number")
        
        if not min_val <= timeout <= max_val:
            raise ValueError(f"Timeout must be between {min_val} and {max_val} seconds")
        
        return True
    
    @staticmethod
    def validate_log_level(level: str) -> bool:
        """
        Validate log level.
        
        Args:
            level: The log level to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If log level is invalid
        """
        if not isinstance(level, str):
            raise ValueError("Log level must be a string")
        
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of: {', '.join(allowed_levels)}")
        
        return True
    
    @staticmethod
    def validate_cors_origins(origins: List[str]) -> bool:
        """
        Validate CORS origins list.
        
        Args:
            origins: List of origin URLs to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If origins are invalid
        """
        if not isinstance(origins, list):
            raise ValueError("CORS origins must be a list")
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        for origin in origins:
            if not isinstance(origin, str):
                raise ValueError("Each CORS origin must be a string")
            
            if origin and not url_pattern.match(origin):
                raise ValueError(f"Invalid CORS origin format: {origin}")
        
        return True
    
    @staticmethod
    def validate_api_url(url: str) -> bool:
        """
        Validate API URL format.
        
        Args:
            url: The API URL to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If URL is invalid
        """
        if not url:
            raise ValueError("API URL cannot be empty")
        
        if not url.startswith(("http://", "https://")):
            raise ValueError("API URL must start with 'http://' or 'https://'")
        
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.hostname:
                raise ValueError("API URL must include hostname")
        except Exception as e:
            raise ValueError(f"Invalid API URL format: {e}")
        
        return True


def validate_config(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Validate a configuration dictionary.
    
    Args:
        config: Dictionary of configuration values to validate
        
    Returns:
        Dict[str, str]: Dictionary of validation errors (empty if all valid)
    """
    errors = {}
    validator = ConfigValidator()
    
    # Database URL validation
    if "DATABASE_URL" in config:
        try:
            validator.validate_database_url(config["DATABASE_URL"])
        except ValueError as e:
            errors["DATABASE_URL"] = str(e)
    
    # OpenAI API key validation
    if "OPENAI_API_KEY" in config:
        try:
            validator.validate_openai_api_key(config["OPENAI_API_KEY"])
        except ValueError as e:
            errors["OPENAI_API_KEY"] = str(e)
    
    # Port validation
    if "PORT" in config:
        try:
            validator.validate_port(config["PORT"])
        except ValueError as e:
            errors["PORT"] = str(e)
    
    # Log level validation
    if "LOG_LEVEL" in config:
        try:
            validator.validate_log_level(config["LOG_LEVEL"])
        except ValueError as e:
            errors["LOG_LEVEL"] = str(e)
    
    # Timeout validations
    for timeout_key in ["OPENAI_TIMEOUT", "DB_CONNECTION_TIMEOUT", "API_REQUEST_TIMEOUT"]:
        if timeout_key in config:
            try:
                validator.validate_timeout(config[timeout_key])
            except ValueError as e:
                errors[timeout_key] = str(e)
    
    # CORS origins validation
    if "ALLOWED_ORIGINS" in config:
        try:
            validator.validate_cors_origins(config["ALLOWED_ORIGINS"])
        except ValueError as e:
            errors["ALLOWED_ORIGINS"] = str(e)
    
    # API URL validation
    if "OPENAI_API_URL" in config:
        try:
            validator.validate_api_url(config["OPENAI_API_URL"])
        except ValueError as e:
            errors["OPENAI_API_URL"] = str(e)
    
    return errors