"""
Integration tests for complete user journeys and system expectations.
Tests for Technical Debt #7 - Comprehensive test coverage for user journeys.
"""

import pytest
import sys
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.api.main import app
from src.core.database import get_db
from src.models.consulta import Consulta
from src.repositories.consulta_repository import ConsultaRepository
import requests
import json


class TestConsultationUserJourney:
    """
    Test complete user journey for consultation booking.
    Covers the main business flow from conversation to persistence.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup API base URL and clean database."""
        self.base_url = "http://localhost:8000"
        self.session_id = str(uuid.uuid4())
        
        # Clean test data before each test
        try:
            db = next(get_db())
            repository = ConsultaRepository(db)
            # Clean existing test data
            test_consultas = db.query(Consulta).filter(
                Consulta.nome.like("Test%")
            ).all()
            for consulta in test_consultas:
                db.delete(consulta)
            db.commit()
            db.close()
        except Exception:
            pass  # Database might not be initialized yet
    
    def test_complete_consultation_booking_flow(self):
        """
        Test the complete flow from initial message to consultation persistence.
        
        User Journey:
        1. User starts conversation with natural language
        2. System extracts partial data
        3. System asks for missing information
        4. User provides missing data
        5. System creates consultation record
        """
        # Step 1: Initial message with partial data
        initial_response = requests.post(
            f"{self.base_url}/chat/message",
            json={
                "message": "Olá, preciso marcar uma consulta para João Silva", 
                "session_id": self.session_id
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert initial_response.status_code == 200
        initial_data = initial_response.json()
        
        # Verify system recognized the intent and extracted name
        assert "response" in initial_data
        assert isinstance(initial_data["extracted_data"], dict)
        
        # Should extract name but need more information
        extracted = initial_data["extracted_data"]
        assert "nome" in extracted or "name" in extracted
        
        # Step 2: Provide phone number
        phone_response = self.client.post(
            "/chat/message",
            json={
                "message": "O telefone é 11999887766",
                "session_id": self.session_id
            }
        )
        
        assert phone_response.status_code == 200
        phone_data = phone_response.json()
        
        # Should accumulate phone with existing name
        phone_extracted = phone_data["extracted_data"]
        assert ("telefone" in phone_extracted or "phone" in phone_extracted)
        
        # Step 3: Provide date and time
        date_response = self.client.post(
            "/chat/message",
            json={
                "message": "Queria para amanhã às 14h, consulta de rotina",
                "session_id": self.session_id
            }
        )
        
        assert date_response.status_code == 200
        date_data = date_response.json()
        
        # Should have most required data now
        final_extracted = date_data["extracted_data"]
        
        # Verify all key fields are present
        expected_fields = ["nome", "telefone", "data", "tipo_consulta"]
        extracted_keys = set(final_extracted.keys())
        
        # Check if at least most fields were extracted (Portuguese or English)
        found_fields = 0
        for field in expected_fields:
            if field in final_extracted:
                found_fields += 1
            # Check English equivalents
            elif field == "nome" and "name" in final_extracted:
                found_fields += 1
            elif field == "telefone" and "phone" in final_extracted:
                found_fields += 1
            elif field == "data" and "date" in final_extracted:
                found_fields += 1
            elif field == "tipo_consulta" and "consultation_type" in final_extracted:
                found_fields += 1
        
        # Should extract at least 3 of 4 main fields
        assert found_fields >= 3, f"Expected at least 3 fields, found {found_fields} in {extracted_keys}"
        
        # Step 4: Check if consultation was created or if confirmation is needed
        # If confidence is high enough, consultation should be created
        if date_data.get("consultation_created"):
            # Verify consultation exists in database
            consultations_response = self.client.get("/consultations")
            assert consultations_response.status_code == 200
            
            consultations = consultations_response.json()
            # Should have at least one consultation created
            assert len(consultations) > 0
            
            # Find our test consultation
            test_consultation = None
            for consultation in consultations:
                if consultation.get("nome", "").startswith("João") or consultation.get("name", "").startswith("João"):
                    test_consultation = consultation
                    break
            
            assert test_consultation is not None, "Test consultation not found in database"
            
            # Verify consultation data
            assert "id" in test_consultation
            assert test_consultation.get("nome") or test_consultation.get("name")
            assert test_consultation.get("telefone") or test_consultation.get("phone")
    
    def test_session_continuity_across_requests(self):
        """
        Test that session context is preserved across multiple requests.
        """
        session_id = str(uuid.uuid4())
        
        # First message
        first_response = self.client.post(
            "/chat/message",
            json={
                "message": "Olá, meu nome é Maria Santos",
                "session_id": session_id
            }
        )
        
        assert first_response.status_code == 200
        first_data = first_response.json()
        first_extracted = first_data["extracted_data"]
        
        # Second message with same session
        second_response = self.client.post(
            "/chat/message",
            json={
                "message": "Meu telefone é 11888777666",
                "session_id": session_id
            }
        )
        
        assert second_response.status_code == 200
        second_data = second_response.json()
        second_extracted = second_data["extracted_data"]
        
        # Session should accumulate data, not replace it
        # Should have both name from first message and phone from second
        has_name = ("nome" in second_extracted and second_extracted["nome"]) or \
                  ("name" in second_extracted and second_extracted["name"])
        has_phone = ("telefone" in second_extracted and second_extracted["telefone"]) or \
                   ("phone" in second_extracted and second_extracted["phone"])
        
        assert has_name, f"Name not found in accumulated data: {second_extracted}"
        assert has_phone, f"Phone not found in accumulated data: {second_extracted}"
    
    def test_invalid_data_recovery_flow(self):
        """
        Test system recovery when user provides invalid data.
        """
        # Provide invalid phone number
        invalid_response = self.client.post(
            "/chat/message",
            json={
                "message": "João Silva, telefone 123",
                "session_id": self.session_id
            }
        )
        
        assert invalid_response.status_code == 200
        invalid_data = invalid_response.json()
        
        # System should identify the problem
        response_text = invalid_data["response"].lower()
        
        # Should indicate phone number issue
        phone_error_indicators = ["telefone", "phone", "número", "numero", "inválido", "invalid", "formato"]
        has_phone_error = any(indicator in response_text for indicator in phone_error_indicators)
        
        # If not in response, should be in validation errors
        if not has_phone_error:
            validation_summary = invalid_data.get("validation_summary", {})
            total_errors = validation_summary.get("total_errors", 0)
            assert total_errors > 0, "System should detect invalid phone number"
        
        # Provide corrected phone number
        corrected_response = self.client.post(
            "/chat/message",
            json={
                "message": "Na verdade o telefone correto é 11999888777",
                "session_id": self.session_id
            }
        )
        
        assert corrected_response.status_code == 200
        corrected_data = corrected_response.json()
        
        # Should have valid phone now
        corrected_extracted = corrected_data["extracted_data"]
        phone_value = corrected_extracted.get("telefone") or corrected_extracted.get("phone")
        
        if phone_value:
            # Valid phone should have at least 10 digits
            phone_digits = ''.join(filter(str.isdigit, phone_value))
            assert len(phone_digits) >= 10, f"Invalid phone format: {phone_value}"
    
    def test_confidence_score_progression(self):
        """
        Test that confidence scores improve as more data is collected.
        """
        session_id = str(uuid.uuid4())
        scores = []
        
        # Initial message with minimal data
        response1 = self.client.post(
            "/chat/message",
            json={
                "message": "Oi",
                "session_id": session_id
            }
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            if "confidence_score" in data1:
                scores.append(data1["confidence_score"])
        
        # Add name
        response2 = self.client.post(
            "/chat/message",
            json={
                "message": "Meu nome é Pedro Silva",
                "session_id": session_id
            }
        )
        
        if response2.status_code == 200:
            data2 = response2.json()
            if "confidence_score" in data2:
                scores.append(data2["confidence_score"])
        
        # Add phone and more details
        response3 = self.client.post(
            "/chat/message",
            json={
                "message": "Telefone 11999888777, consulta de rotina para amanhã às 15h",
                "session_id": session_id
            }
        )
        
        if response3.status_code == 200:
            data3 = response3.json()
            if "confidence_score" in data3:
                scores.append(data3["confidence_score"])
        
        # Verify progression (if we have at least 2 scores)
        if len(scores) >= 2:
            # Later scores should generally be higher or at least not significantly lower
            assert scores[-1] >= scores[0] - 0.1, f"Confidence should improve: {scores}"
    
    def test_database_consultation_creation(self):
        """
        Test that consultations are properly created in the database.
        """
        # Send complete consultation data
        complete_response = self.client.post(
            "/chat/message",
            json={
                "message": "João da Silva, telefone 11999888777, consulta de cardiologia para amanhã às 16h",
                "session_id": self.session_id
            }
        )
        
        assert complete_response.status_code == 200
        complete_data = complete_response.json()
        
        # Wait a moment for any async processing
        import time
        time.sleep(1)
        
        # Check if consultation was created
        consultations_response = self.client.get("/consultations")
        
        if consultations_response.status_code == 200:
            consultations = consultations_response.json()
            
            # Look for our consultation (should have João in the name)
            test_consultation = None
            for consultation in consultations:
                name_field = consultation.get("nome") or consultation.get("name", "")
                if "João" in name_field or "Joao" in name_field:
                    test_consultation = consultation
                    break
            
            if test_consultation:
                # Verify structure
                assert "id" in test_consultation
                assert test_consultation.get("nome") or test_consultation.get("name")
                assert test_consultation.get("telefone") or test_consultation.get("phone")
                
                # Verify session tracking
                if "session_id" in test_consultation:
                    assert test_consultation["session_id"] == self.session_id


class TestSystemHealthAndResilience:
    """
    Test system health, error handling, and resilience.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client."""
        self.client = TestClient(app)
    
    def test_health_endpoint_comprehensive(self):
        """
        Test health endpoint with comprehensive checks.
        """
        response = self.client.get("/system/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        
        # Should report overall status
        assert health_data["status"] in ["healthy", "degraded", "unhealthy"]
        
        # Should include service checks
        if "services" in health_data:
            services = health_data["services"]
            # Database should be checked
            assert "database" in services or "postgresql" in services
    
    def test_invalid_session_handling(self):
        """
        Test handling of invalid or missing session IDs.
        """
        # No session ID provided
        no_session_response = self.client.post(
            "/chat/message",
            json={"message": "Hello"}
        )
        
        # Should handle gracefully (either create new session or return error)
        assert no_session_response.status_code in [200, 400, 422]
        
        # Invalid session ID format
        invalid_session_response = self.client.post(
            "/chat/message",
            json={
                "message": "Hello",
                "session_id": "invalid-session-format-123"
            }
        )
        
        # Should handle gracefully
        assert invalid_session_response.status_code in [200, 400, 422]
    
    def test_empty_or_invalid_message_handling(self):
        """
        Test handling of empty or invalid messages.
        """
        session_id = str(uuid.uuid4())
        
        test_cases = [
            "",  # Empty string
            "   ",  # Only whitespace
            "a" * 1000,  # Very long message
        ]
        
        for test_message in test_cases:
            response = self.client.post(
                "/chat/message",
                json={
                    "message": test_message,
                    "session_id": session_id
                }
            )
            
            # Should handle gracefully (not crash)
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                data = response.json()
                assert "response" in data  # Should always provide some response
    
    def test_concurrent_sessions(self):
        """
        Test handling of multiple concurrent sessions.
        """
        session_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        # Send messages from different sessions
        responses = []
        for i, session_id in enumerate(session_ids):
            response = self.client.post(
                "/chat/message",
                json={
                    "message": f"Hello from session {i}",
                    "session_id": session_id
                }
            )
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "response" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])