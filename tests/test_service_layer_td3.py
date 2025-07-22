"""
Tests for Service Layer Architecture (Technical Debt #3 resolution).

This test suite validates the service layer improvements including:
- Service dependency injection
- Singleton pattern compliance
- Error handling consistency
- Cross-service integration
"""

import pytest
from unittest.mock import Mock, patch
from src.core.container import ServiceContainer, get_chat_service, get_validation_service, get_extraction_service, get_session_service


class TestServiceLayerArchitecture:
    """Test suite for service layer architecture improvements."""
    
    def test_service_container_singleton(self):
        """Test that ServiceContainer implements proper singleton pattern."""
        container1 = ServiceContainer()
        container2 = ServiceContainer()
        
        assert container1 is container2, "ServiceContainer should be singleton"
    
    def test_service_container_lazy_initialization(self):
        """Test that services are initialized lazily."""
        container = ServiceContainer()
        container.clear_services()  # Clear for clean test
        
        # Services should not be initialized until requested
        assert not container.is_initialized('chat_service')
        assert not container.is_initialized('validation_service')
        
        # Getting service should initialize it
        chat_service = container.get_service('chat_service')
        assert container.is_initialized('chat_service')
        assert chat_service is not None
    
    def test_dependency_injection_consistency(self):
        """Test that services use proper dependency injection."""
        container = ServiceContainer()
        container.clear_services()
        
        # Get services that should share dependencies
        extraction_service = container.get_service('extraction_service')
        consultation_service = container.get_service('consultation_service')
        
        # Both should share the same EntityExtractor instance
        assert extraction_service.entity_extractor is consultation_service.entity_extractor
    
    def test_service_convenience_functions(self):
        """Test that convenience functions work correctly."""
        chat_service1 = get_chat_service()
        chat_service2 = get_chat_service()
        
        # Should return same instance (singleton)
        assert chat_service1 is chat_service2
        
        # Test other convenience functions
        validation_service = get_validation_service()
        extraction_service = get_extraction_service()
        session_service = get_session_service()
        
        assert validation_service is not None
        assert extraction_service is not None
        assert session_service is not None
    
    @pytest.mark.asyncio
    async def test_validation_service_error_handling(self):
        """Test ValidationService error handling improvements."""
        validation_service = get_validation_service()
        
        # Test that ValidationService structure works correctly
        test_data = {
            "nome": "João Silva",
            "telefone": "81999887766",  # Valid phone  
            "data": "2025-12-25",  # Future date
            "horario": "14:00"  # Valid time
        }
        
        result = await validation_service.validate_consultation_data(test_data)
        
        # Should handle data correctly
        assert result["success"] is True
        assert "business_rules" in result
        assert "warnings" in result["business_rules"]  # This was the bug we fixed - ensuring warnings key exists
        assert "violations" in result["business_rules"]
        assert "field_validations" in result
        assert "normalized_data" in result
    
    def test_chat_service_dependency_injection(self):
        """Test ChatService uses injected SessionService."""
        container = ServiceContainer()
        container.clear_services()
        
        # Get ChatService - should initialize SessionService automatically
        chat_service = container.get_service('chat_service')
        session_service = container.get_service('session_service')
        
        # ChatService should use the same SessionService instance
        assert chat_service.session_service is session_service
    
    @pytest.mark.asyncio
    async def test_service_layer_integration(self):
        """Test that services work together correctly."""
        container = ServiceContainer()
        
        # Test basic integration flow
        chat_service = container.get_service('chat_service')
        
        # Process a simple message
        result = await chat_service.process_message("Olá, gostaria de agendar uma consulta")
        
        # Should return proper response structure
        assert "response" in result
        assert "session_id" in result
        assert "action" in result
        assert "extracted_data" in result
        assert "confidence" in result
    
    def test_service_registration_and_override(self):
        """Test manual service registration for testing."""
        container = ServiceContainer()
        
        # Register mock service
        mock_service = Mock()
        container.register_service('test_service', mock_service)
        
        # Should return mock service
        retrieved_service = container.get_service('test_service')
        assert retrieved_service is mock_service
    
    def test_service_clear_functionality(self):
        """Test service clearing for clean testing state."""
        container = ServiceContainer()
        
        # Initialize a service
        container.get_service('validation_service')
        assert container.is_initialized('validation_service')
        
        # Clear services
        container.clear_services()
        assert not container.is_initialized('validation_service')
    
    @pytest.mark.asyncio
    async def test_extraction_service_context_awareness(self):
        """Test ExtractionService context enhancement."""
        extraction_service = get_extraction_service()
        
        # Test with context
        context = {
            "extracted_data": {
                "nome": "João Silva",
                "telefone": "81999887766"
            }
        }
        
        # Should enhance message with context
        enhanced_message = extraction_service._enhance_message_with_context(
            "Quero marcar para amanhã às 14h", context
        )
        
        assert "João Silva" in enhanced_message
        assert "81999887766" in enhanced_message
        assert "Quero marcar para amanhã às 14h" in enhanced_message


class TestServiceLayerErrorHandling:
    """Test error handling across service layer."""
    
    @pytest.mark.asyncio
    async def test_validation_service_handles_malformed_data(self):
        """Test ValidationService handles malformed data gracefully."""
        validation_service = get_validation_service()
        
        # Test with malformed data types
        malformed_data = {
            "nome": ["not", "a", "string"],
            "telefone": {"invalid": "structure"},
            "data": None
        }
        
        result = await validation_service.validate_consultation_data(malformed_data)
        
        # Should handle gracefully without crashing
        assert "success" in result
        assert "metadata" in result
        assert "validation_timestamp" in result["metadata"]
    
    @pytest.mark.asyncio 
    async def test_chat_service_handles_llm_errors(self):
        """Test ChatService handles LLM service errors gracefully."""
        chat_service = get_chat_service()
        
        # Test with a problematic message that should trigger fallback
        result = await chat_service.process_message("Invalid test message")
        
        # Should handle gracefully using reasoning coordinator fallback
        assert result["action"] in ["extract", "ask", "fallback"]  # Valid actions
        assert "response" in result
        assert "confidence" in result
        assert result["confidence"] >= 0.0  # Should be valid confidence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])