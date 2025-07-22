"""
Service Container for dependency injection and singleton management.

This module provides a centralized way to manage service instances,
eliminating duplicate initializations and facilitating testing through
dependency injection.
"""

from typing import Dict, Any, Optional, TypeVar, Type
import threading
from src.core.openai_client import OpenAIClient
from src.core.entity_extraction import EntityExtractor
from src.core.reasoning.reasoning_coordinator import ReasoningCoordinator
from src.services.consultation_service import ConsultationService

T = TypeVar('T')


class ServiceContainer:
    """
    Singleton service container for managing application dependencies.
    
    Provides centralized initialization and retrieval of service instances,
    with lazy loading and thread-safe singleton pattern.
    """
    
    _instance: Optional['ServiceContainer'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'ServiceContainer':
        """Ensure singleton pattern with thread safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
                    cls._instance._services: Dict[str, Any] = {}
        return cls._instance
    
    def __init__(self):
        """Initialize container (only once due to singleton pattern)."""
        if not hasattr(self, '_initialized') or not self._initialized:
            self._services: Dict[str, Any] = {}
            self._initialized = True
    
    def initialize_services(self) -> None:
        """
        Initialize all core services with proper dependency order.
        
        Services are initialized in dependency order:
        1. OpenAIClient (no dependencies)
        2. EntityExtractor (depends on OpenAIClient)
        3. ReasoningCoordinator (no external dependencies)
        4. ConsultationService (depends on EntityExtractor)
        """
        if 'openai_client' not in self._services:
            self._services['openai_client'] = OpenAIClient()
        
        if 'entity_extractor' not in self._services:
            # Inject OpenAI client to avoid duplication
            openai_client = self._services['openai_client']
            self._services['entity_extractor'] = EntityExtractor(openai_client=openai_client)
        
        if 'reasoning_coordinator' not in self._services:
            # ReasoningCoordinator doesn't need external dependencies
            self._services['reasoning_coordinator'] = ReasoningCoordinator()
        
        if 'consultation_service' not in self._services:
            # Inject shared EntityExtractor to avoid duplication
            entity_extractor = self._services['entity_extractor']
            self._services['consultation_service'] = ConsultationService(
                entity_extractor=entity_extractor
            )
    
    def get_service(self, service_name: str) -> Any:
        """
        Get a service instance by name.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service is not registered
        """
        if service_name not in self._services:
            # Lazy initialization
            self.initialize_services()
        
        if service_name not in self._services:
            raise KeyError(f"Service '{service_name}' not found in container")
        
        return self._services[service_name]
    
    def register_service(self, service_name: str, service_instance: Any) -> None:
        """
        Register a service instance manually.
        
        Useful for testing or custom service configurations.
        
        Args:
            service_name: Name to register the service under
            service_instance: Instance to register
        """
        self._services[service_name] = service_instance
    
    def clear_services(self) -> None:
        """
        Clear all registered services.
        
        Primarily used for testing to ensure clean state.
        """
        self._services.clear()
    
    def is_initialized(self, service_name: str) -> bool:
        """
        Check if a service is already initialized.
        
        Args:
            service_name: Name of service to check
            
        Returns:
            True if service is initialized, False otherwise
        """
        return service_name in self._services


# Convenience functions for common services
def get_openai_client() -> OpenAIClient:
    """Get the singleton OpenAI client instance."""
    container = ServiceContainer()
    return container.get_service('openai_client')


def get_entity_extractor() -> EntityExtractor:
    """Get the singleton EntityExtractor instance."""
    container = ServiceContainer()
    return container.get_service('entity_extractor')


def get_reasoning_coordinator() -> ReasoningCoordinator:
    """Get the singleton ReasoningCoordinator instance."""
    container = ServiceContainer()
    return container.get_service('reasoning_coordinator')


def get_consultation_service() -> ConsultationService:
    """Get the singleton ConsultationService instance."""
    container = ServiceContainer()
    return container.get_service('consultation_service')


# Global container instance for easy access
container = ServiceContainer()