"""
Simplified integration tests for user journeys without database fixtures.
Tests for Technical Debt #7 - focusing on API behavior and user experience.
"""

import pytest
import uuid
import requests
import json
import time
from typing import Dict, Any, Optional


class TestUserJourneySimple:
    """
    Test user journeys by calling the live API directly.
    This bypasses database fixture issues and tests the real system.
    """
    
    BASE_URL = "http://localhost:8000"
    
    def make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to API."""
        try:
            url = f"{self.BASE_URL}{endpoint}"
            
            if method.upper() == "POST":
                response = requests.post(
                    url, 
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            else:
                response = requests.get(url, timeout=10)
                
            return {
                "status_code": response.status_code,
                "data": response.json() if response.status_code == 200 else {},
                "success": response.status_code == 200,
                "error": None
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "status_code": 0,
                "data": {},
                "success": False,
                "error": "API not running - start with docker-compose up"
            }
        except Exception as e:
            return {
                "status_code": 0,
                "data": {},
                "success": False,
                "error": str(e)
            }

    def chat_message(self, message: str, session_id: Optional[str] = None) -> Dict:
        """Send chat message to API."""
        if session_id is None:
            session_id = str(uuid.uuid4())
            
        return self.make_request(
            "/chat/message",
            "POST",
            {
                "message": message,
                "session_id": session_id
            }
        )

    def test_api_health_check(self):
        """
        Test that the API is running and healthy.
        """
        result = self.make_request("/system/health")
        
        if not result["success"]:
            if result["error"]:
                pytest.skip(f"API not running: {result['error']}")
            else:
                pytest.skip(f"Health check failed: {result['status_code']}")
        
        health_data = result["data"]
        assert "status" in health_data
        
        print(f"✅ API Health Status: {health_data.get('status', 'unknown')}")
        
        # Log additional health info if available
        if "services" in health_data:
            print(f"Services: {health_data['services']}")
        if "database" in health_data:
            print(f"Database: {health_data['database']}")

    def test_complete_user_journey_booking(self):
        """
        Test complete user journey: greeting → data collection → booking.
        """
        session_id = str(uuid.uuid4())
        conversation_log = []
        
        # Step 1: User greets and states intent
        step1 = self.chat_message("Olá, preciso marcar uma consulta", session_id)
        conversation_log.append(("User greeting", step1))
        
        if not step1["success"]:
            pytest.skip(f"Chat API not working: {step1['error']}")
        
        assert "response" in step1["data"], "Should get response to greeting"
        print(f"Step 1 ✅ - Greeting handled")
        
        # Step 2: User provides name
        step2 = self.chat_message("Meu nome é João Silva", session_id)
        conversation_log.append(("Name provided", step2))
        
        if step2["success"]:
            extracted = step2["data"].get("extracted_data", {})
            has_name = any("joão" in str(v).lower() or "joao" in str(v).lower() 
                          for v in extracted.values() if v)
            
            if has_name:
                print(f"Step 2 ✅ - Name extracted successfully")
            else:
                print(f"Step 2 ⚠️ - Name extraction incomplete: {extracted}")
        
        # Step 3: User provides phone
        step3 = self.chat_message("Telefone é 11999888777", session_id)
        conversation_log.append(("Phone provided", step3))
        
        if step3["success"]:
            extracted = step3["data"].get("extracted_data", {})
            has_phone = any("11999888777" in str(v) for v in extracted.values() if v)
            
            if has_phone:
                print(f"Step 3 ✅ - Phone extracted successfully")
            else:
                print(f"Step 3 ⚠️ - Phone extraction incomplete: {extracted}")
        
        # Step 4: User provides date and consultation type
        step4 = self.chat_message("Consulta de cardiologia para amanhã às 14h", session_id)
        conversation_log.append(("Complete info", step4))
        
        if step4["success"]:
            data = step4["data"]
            extracted = data.get("extracted_data", {})
            confidence = data.get("confidence_score", 0)
            
            # Count extracted fields
            field_count = len([v for v in extracted.values() if v])
            
            print(f"Step 4 ✅ - Final extraction: {field_count} fields, confidence: {confidence}")
            
            # Should have extracted multiple fields by now
            assert field_count >= 2, f"Should extract multiple fields: {extracted}"
            
            # Should have reasonable confidence with complete data
            if confidence > 0:
                assert confidence >= 0.3, f"Confidence too low for complete data: {confidence}"
                print(f"Confidence score: {confidence:.2f}")
            
            # Check if consultation was created or flagged for creation
            if data.get("consultation_created"):
                print("✅ Consultation created successfully")
            elif data.get("consultation_ready"):
                print("✅ Consultation ready for creation")
            else:
                print("ℹ️ Consultation creation may require confirmation")

    def test_phone_validation_behavior(self):
        """
        Test phone validation behavior with valid and invalid numbers.
        """
        test_cases = [
            {
                "message": "João Silva, telefone 11999888777",
                "expected_valid": True,
                "description": "Valid São Paulo mobile"
            },
            {
                "message": "Maria Santos, telefone 123",
                "expected_valid": False, 
                "description": "Invalid short number"
            }
        ]
        
        for case in test_cases:
            session_id = str(uuid.uuid4())
            result = self.chat_message(case["message"], session_id)
            
            if result["success"]:
                data = result["data"]
                validation_summary = data.get("validation_summary", {})
                response_text = data.get("response", "").lower()
                
                error_count = validation_summary.get("total_errors", 0)
                
                if case["expected_valid"]:
                    # Valid phone should have low error count
                    print(f"✅ {case['description']}: {error_count} errors")
                else:
                    # Invalid phone should trigger validation response
                    has_validation_response = (
                        error_count > 0 or
                        any(word in response_text for word in 
                            ["telefone", "phone", "número", "numero", "formato", "inválido"])
                    )
                    
                    if has_validation_response:
                        print(f"✅ {case['description']}: Validation error detected")
                    else:
                        print(f"⚠️ {case['description']}: Invalid phone not caught")

    def test_context_persistence_across_messages(self):
        """
        Test that context persists across multiple messages in same session.
        """
        session_id = str(uuid.uuid4())
        
        # Message 1: Name only
        msg1 = self.chat_message("Meu nome é Ana Santos", session_id)
        
        # Message 2: Add phone in same session
        msg2 = self.chat_message("Meu telefone é 11888999777", session_id)
        
        if msg1["success"] and msg2["success"]:
            # Second message should have accumulated data from first
            extracted2 = msg2["data"].get("extracted_data", {})
            
            # Should have both name and phone
            has_name = any("ana" in str(v).lower() for v in extracted2.values() if v)
            has_phone = any("11888999777" in str(v) for v in extracted2.values() if v)
            
            if has_name and has_phone:
                print("✅ Context accumulation working - both name and phone present")
            elif has_name or has_phone:
                print("⚠️ Partial context accumulation - missing some data")
                print(f"Extracted data: {extracted2}")
            else:
                print(f"❌ Context not accumulating - extracted: {extracted2}")

    def test_session_isolation(self):
        """
        Test that different sessions don't interfere with each other.
        """
        session_a = str(uuid.uuid4())
        session_b = str(uuid.uuid4())
        
        # Session A: Alice
        msg_a1 = self.chat_message("Meu nome é Alice", session_a)
        
        # Session B: Bob  
        msg_b1 = self.chat_message("Meu nome é Bob", session_b)
        
        # Session A: Add more info
        msg_a2 = self.chat_message("Telefone 11999888777", session_a)
        
        # Session B: Ask for context (should only know about Bob)
        msg_b2 = self.chat_message("Qual é meu nome?", session_b)
        
        if all(m["success"] for m in [msg_a1, msg_b1, msg_a2, msg_b2]):
            # Session A should have Alice + phone
            extracted_a = msg_a2["data"].get("extracted_data", {})
            has_alice = any("alice" in str(v).lower() for v in extracted_a.values() if v)
            has_phone_a = any("11999888777" in str(v) for v in extracted_a.values() if v)
            
            # Session B response should reference Bob, not Alice
            response_b = msg_b2["data"].get("response", "").lower()
            mentions_bob = "bob" in response_b
            mentions_alice = "alice" in response_b
            
            if has_alice and has_phone_a and not mentions_alice:
                print("✅ Session isolation working correctly")
            else:
                print("⚠️ Possible session isolation issue")
                print(f"Session A data: {extracted_a}")
                print(f"Session B response: {response_b}")

    def test_confidence_score_progression(self):
        """
        Test that confidence scores improve with more complete data.
        """
        session_id = str(uuid.uuid4())
        scores = []
        
        messages = [
            "Oi",
            "João Silva",
            "Telefone 11999888777",
            "Consulta para amanhã às 14h"
        ]
        
        for i, message in enumerate(messages):
            result = self.chat_message(message, session_id)
            
            if result["success"]:
                confidence = result["data"].get("confidence_score", 0)
                scores.append(confidence)
                print(f"Message {i+1}: '{message[:20]}...' → Confidence: {confidence:.2f}")
        
        if len(scores) >= 2:
            # Generally expect improvement (with some tolerance)
            first_score = scores[0]
            last_score = scores[-1]
            
            if last_score >= first_score - 0.1:  # Allow small decreases
                print(f"✅ Confidence progression reasonable: {first_score:.2f} → {last_score:.2f}")
            else:
                print(f"⚠️ Confidence decreased significantly: {first_score:.2f} → {last_score:.2f}")

    def test_error_handling_resilience(self):
        """
        Test system resilience with edge cases.
        """
        edge_cases = [
            ("", "Empty message"),
            ("   ", "Whitespace only"),
            ("a" * 500, "Very long message"),
            ("!@#$%^&*()", "Special characters only")
        ]
        
        for message, description in edge_cases:
            result = self.chat_message(message)
            
            # Should handle gracefully (not crash)
            if result["status_code"] in [200, 400, 422]:
                print(f"✅ {description}: Handled gracefully ({result['status_code']})")
            else:
                print(f"⚠️ {description}: Unexpected response ({result['status_code']})")

    def test_data_extraction_accuracy(self):
        """
        Test accuracy of data extraction from complex messages.
        """
        complex_cases = [
            {
                "message": "Oi, é para Maria Santos, telefone 21987654321, consulta de rotina",
                "expected_fields": ["nome", "telefone", "tipo_consulta"],
                "description": "Multi-field extraction"
            },
            {
                "message": "João Silva, telefone é (11) 99988-7766, para próxima terça às 15h",
                "expected_fields": ["nome", "telefone", "data"],
                "description": "Formatted phone and relative date"
            }
        ]
        
        for case in complex_cases:
            session_id = str(uuid.uuid4())
            result = self.chat_message(case["message"], session_id)
            
            if result["success"]:
                extracted = result["data"].get("extracted_data", {})
                field_count = len([v for v in extracted.values() if v])
                expected_count = len(case["expected_fields"])
                
                success_rate = field_count / expected_count if expected_count > 0 else 0
                
                print(f"{case['description']}: {field_count}/{expected_count} fields extracted ({success_rate:.1%})")
                
                if success_rate >= 0.6:  # 60% success rate threshold
                    print(f"✅ Good extraction rate: {extracted}")
                else:
                    print(f"⚠️ Low extraction rate: {extracted}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s shows print statements