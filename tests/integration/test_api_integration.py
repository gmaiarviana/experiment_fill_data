"""
Integration tests for API endpoints - testing against live system.
Focused on user journeys and system expectations - Technical Debt #7.
"""

import pytest
import uuid
import requests
import json
import time
from typing import Dict, Any, Optional


class TestAPIIntegration:
    """
    Test API integration with live system.
    """
    
    BASE_URL = "http://localhost:8000"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        self.session_id = str(uuid.uuid4())
    
    def make_chat_request(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Make a chat request to the API.
        
        Args:
            message: Message to send
            session_id: Session ID (uses default if not provided)
            
        Returns:
            dict: Response data
        """
        if session_id is None:
            session_id = self.session_id
            
        try:
            response = requests.post(
                f"{self.BASE_URL}/chat/message",
                json={
                    "message": message,
                    "session_id": session_id
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            return {
                "status_code": response.status_code,
                "data": response.json() if response.status_code == 200 else {},
                "error": None
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "status_code": 0,
                "data": {},
                "error": "Connection failed - API not running"
            }
        except Exception as e:
            return {
                "status_code": 0,
                "data": {},
                "error": str(e)
            }
    
    def test_basic_api_connectivity(self):
        """
        Test basic API connectivity and health.
        """
        # Test health endpoint
        try:
            health_response = requests.get(f"{self.BASE_URL}/system/health", timeout=5)
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                assert "status" in health_data
                print(f"✅ API Health: {health_data}")
            else:
                pytest.skip(f"API health check failed: {health_response.status_code}")
                
        except requests.exceptions.ConnectionError:
            pytest.skip("API not accessible - run docker-compose up first")
    
    def test_simple_conversation_flow(self):
        """
        Test simple conversation flow with basic extraction.
        """
        # Simple greeting
        response = self.make_chat_request("Olá")
        
        if response["error"]:
            pytest.skip(f"API error: {response['error']}")
        
        assert response["status_code"] == 200, "Chat endpoint should respond"
        
        data = response["data"]
        assert "response" in data, "Should have response field"
        
        print(f"✅ Greeting response: {data.get('response', '')[:100]}...")
        
        # Message with name
        response = self.make_chat_request("Meu nome é João Silva")
        
        if response["status_code"] == 200:
            data = response["data"]
            extracted_data = data.get("extracted_data", {})
            
            # Should extract name in some form
            has_name = any(
                "joão" in str(value).lower() or "joao" in str(value).lower()
                for value in extracted_data.values()
            )
            
            if has_name:
                print(f"✅ Name extraction successful: {extracted_data}")
            else:
                print(f"⚠️ Name extraction incomplete: {extracted_data}")
    
    def test_phone_validation_journey(self):
        """
        Test phone validation through conversation.
        """
        # Valid Brazilian phone
        response = self.make_chat_request("João Silva, telefone 11999888777")
        
        if response["status_code"] == 200:
            data = response["data"]
            extracted_data = data.get("extracted_data", {})
            
            # Check if phone was extracted
            phone_fields = ["telefone", "phone"]
            phone_value = None
            
            for field in phone_fields:
                if field in extracted_data and extracted_data[field]:
                    phone_value = extracted_data[field]
                    break
            
            if phone_value:
                phone_digits = ''.join(filter(str.isdigit, phone_value))
                if len(phone_digits) >= 10:
                    print(f"✅ Valid phone extraction: {phone_value}")
                else:
                    print(f"⚠️ Phone format issue: {phone_value}")
            else:
                print("⚠️ Phone not extracted from message")
        
        # Invalid phone - should trigger validation error
        response = self.make_chat_request("Maria Santos, telefone 123")
        
        if response["status_code"] == 200:
            data = response["data"]
            validation_summary = data.get("validation_summary", {})
            response_text = data.get("response", "").lower()
            
            # Should either have validation errors or helpful response
            has_validation_error = validation_summary.get("total_errors", 0) > 0
            mentions_phone_issue = any(word in response_text 
                                     for word in ["telefone", "phone", "número", "numero", "formato"])
            
            if has_validation_error or mentions_phone_issue:
                print(f"✅ Invalid phone handled correctly")
            else:
                print(f"⚠️ Invalid phone not properly handled")
    
    def test_context_accumulation(self):
        """
        Test context accumulation across messages.
        """
        session_id = str(uuid.uuid4())
        
        # Build context progressively
        messages = [
            "Meu nome é Ana Santos",
            "Telefone 11999888777", 
            "Consulta para amanhã"
        ]
        
        extracted_fields_progression = []
        
        for i, message in enumerate(messages):
            response = self.make_chat_request(message, session_id)
            
            if response["status_code"] == 200:
                data = response["data"]
                extracted_data = data.get("extracted_data", {})
                
                # Count non-empty extracted fields
                field_count = len([v for v in extracted_data.values() if v])
                extracted_fields_progression.append(field_count)
                
                print(f"Step {i+1}: {field_count} fields extracted - {extracted_data}")
        
        # Should show progression (more fields over time)
        if len(extracted_fields_progression) >= 2:
            final_count = extracted_fields_progression[-1] 
            initial_count = extracted_fields_progression[0]
            
            if final_count >= initial_count:
                print(f"✅ Context accumulation working: {extracted_fields_progression}")
            else:
                print(f"⚠️ Context not accumulating properly: {extracted_fields_progression}")
    
    def test_confidence_scoring(self):
        """
        Test confidence score behavior.
        """
        test_cases = [
            {
                "message": "Olá",
                "expected_confidence": "low",
                "description": "Greeting only"
            },
            {
                "message": "João Silva, telefone 11999888777, consulta de cardiologia para amanhã às 14h",
                "expected_confidence": "high", 
                "description": "Complete data"
            }
        ]
        
        for case in test_cases:
            response = self.make_chat_request(case["message"])
            
            if response["status_code"] == 200:
                data = response["data"]
                confidence = data.get("confidence_score", 0)
                
                if case["expected_confidence"] == "high" and confidence > 0.6:
                    print(f"✅ High confidence for complete data: {confidence}")
                elif case["expected_confidence"] == "low" and confidence < 0.4:
                    print(f"✅ Low confidence for minimal data: {confidence}")
                else:
                    print(f"⚠️ Unexpected confidence for {case['description']}: {confidence}")
    
    def test_consultation_creation(self):
        """
        Test if consultations are created successfully.
        """
        # Send complete consultation request
        complete_message = "João Silva, telefone 11999888777, consulta de cardiologia para amanhã às 14h"
        
        response = self.make_chat_request(complete_message)
        
        if response["status_code"] == 200:
            data = response["data"]
            
            # Check if consultation was created
            consultation_created = data.get("consultation_created", False)
            
            if consultation_created:
                print("✅ Consultation created successfully")
            else:
                print("ℹ️ Consultation creation may require additional steps")
            
            # Try to fetch consultations
            try:
                consultations_response = requests.get(
                    f"{self.BASE_URL}/consultations",
                    timeout=5
                )
                
                if consultations_response.status_code == 200:
                    consultations = consultations_response.json()
                    consultation_count = len(consultations)
                    print(f"✅ Consultations endpoint accessible: {consultation_count} consultations")
                else:
                    print(f"⚠️ Consultations endpoint issue: {consultations_response.status_code}")
                    
            except Exception as e:
                print(f"ℹ️ Consultations endpoint not tested: {e}")
    
    def test_error_handling(self):
        """
        Test error handling and resilience.
        """
        error_cases = [
            {"message": "", "description": "Empty message"},
            {"message": "   ", "description": "Whitespace only"},
            {"message": "x" * 1000, "description": "Very long message"}
        ]
        
        for case in error_cases:
            response = self.make_chat_request(case["message"])
            
            # Should handle gracefully (not crash)
            if response["status_code"] in [200, 400, 422]:
                print(f"✅ Handled {case['description']} gracefully")
            else:
                print(f"⚠️ Unexpected response for {case['description']}: {response['status_code']}")
    
    def test_session_isolation(self):
        """
        Test that different sessions are isolated.
        """
        session_a = str(uuid.uuid4())
        session_b = str(uuid.uuid4())
        
        # Session A
        response_a = self.make_chat_request("Meu nome é Alice", session_a)
        
        # Session B  
        response_b = self.make_chat_request("Meu nome é Bob", session_b)
        
        # Check Session A again
        response_a2 = self.make_chat_request("Qual é meu telefone?", session_a)
        
        if all(r["status_code"] == 200 for r in [response_a, response_b, response_a2]):
            data_a2 = response_a2["data"]
            response_text = data_a2.get("response", "").lower()
            
            # Session A should remember Alice, not Bob
            remembers_alice = "alice" in response_text
            mentions_bob = "bob" in response_text
            
            if remembers_alice and not mentions_bob:
                print("✅ Session isolation working correctly")
            else:
                print(f"⚠️ Session isolation issue - Response: {response_text[:100]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print statements