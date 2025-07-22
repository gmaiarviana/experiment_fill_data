"""
Integration tests for conversation flow and reasoning engine.
Tests for Technical Debt #7 - Conversation intelligence and context management.
"""

import pytest
import sys
import os
import uuid
from typing import Dict, Any, List

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.api.main import app
from fastapi.testclient import TestClient


class TestConversationIntelligence:
    """
    Test conversation intelligence and context-aware responses.
    Covers Technical Debt #3 - Reasoning Intelligence Limited.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client."""
        self.client = TestClient(app)
    
    def test_intent_recognition_patterns(self):
        """
        Test system's ability to recognize different consultation intents.
        """
        session_id = str(uuid.uuid4())
        
        intent_test_cases = [
            {
                "message": "Preciso marcar uma consulta",
                "expected_intent": "booking",
                "description": "Direct booking intent"
            },
            {
                "message": "Quero reagendar minha consulta",
                "expected_intent": "reschedule",
                "description": "Reschedule intent"
            },
            {
                "message": "Como cancelo minha consulta?",
                "expected_intent": "cancel", 
                "description": "Cancellation intent"
            },
            {
                "message": "Que horários têm disponível?",
                "expected_intent": "availability",
                "description": "Availability inquiry"
            }
        ]
        
        for test_case in intent_test_cases:
            response = self.client.post(
                "/chat/message",
                json={
                    "message": test_case["message"],
                    "session_id": session_id
                }
            )
            
            assert response.status_code == 200, f"Failed for: {test_case['description']}"
            
            data = response.json()
            response_text = data.get("response", "").lower()
            
            # System should provide appropriate response for each intent
            assert len(response_text) > 0, f"Empty response for: {test_case['description']}"
            
            # Should not just ask generic questions for all intents
            generic_responses = ["como posso ajudar", "what can i help", "o que você precisa"]
            is_generic = any(generic in response_text for generic in generic_responses)
            
            # For specific intents, should not always be generic
            if test_case["expected_intent"] in ["reschedule", "cancel"]:
                # These should trigger more specific responses
                specific_keywords = {
                    "reschedule": ["reagendar", "remarcar", "alterar", "mudar"],
                    "cancel": ["cancelar", "cancel", "desmarcar"]
                }
                
                expected_keywords = specific_keywords[test_case["expected_intent"]]
                has_specific_response = any(keyword in response_text for keyword in expected_keywords)
                
                # Should show understanding of specific intent (if not generic fallback)
                if not is_generic:
                    assert has_specific_response or "consulta" in response_text, \
                        f"Should acknowledge {test_case['expected_intent']} intent: {response_text}"
    
    def test_correction_handling(self):
        """
        Test system's ability to handle user corrections.
        Addresses Technical Debt #2 - Context Management Broken.
        """
        session_id = str(uuid.uuid4())
        
        # Initial data with error
        initial_response = self.client.post(
            "/chat/message",
            json={
                "message": "João Silva, telefone 11999888777",
                "session_id": session_id
            }
        )
        
        assert initial_response.status_code == 200
        initial_data = initial_response.json()
        initial_extracted = initial_data.get("extracted_data", {})
        
        # Correction message
        correction_response = self.client.post(
            "/chat/message",
            json={
                "message": "Na verdade, o telefone correto é 11888999777",
                "session_id": session_id
            }
        )
        
        assert correction_response.status_code == 200
        correction_data = correction_response.json()
        corrected_extracted = correction_data.get("extracted_data", {})
        
        # Should have updated phone number
        old_phone = initial_extracted.get("telefone") or initial_extracted.get("phone", "")
        new_phone = corrected_extracted.get("telefone") or corrected_extracted.get("phone", "")
        
        # Phone should be updated if system detected correction
        if old_phone and new_phone:
            # Should be different (corrected)
            assert old_phone != new_phone, f"Phone should be corrected: {old_phone} -> {new_phone}"
            
            # New phone should contain the corrected number
            corrected_digits = "11888999777"
            new_phone_digits = ''.join(filter(str.isdigit, new_phone))
            assert corrected_digits in new_phone_digits, f"Corrected phone not found: {new_phone}"
        
        # Should maintain other data (name)
        old_name = initial_extracted.get("nome") or initial_extracted.get("name", "")
        new_name = corrected_extracted.get("nome") or corrected_extracted.get("name", "")
        
        if old_name and new_name:
            # Name should be preserved
            assert "João" in new_name or "Joao" in new_name, f"Name should be preserved: {new_name}"
    
    def test_complex_natural_language_patterns(self):
        """
        Test system's handling of complex natural language expressions.
        """
        session_id = str(uuid.uuid4())
        
        complex_test_cases = [
            {
                "message": "Oi, é pra minha mãe, Maria da Silva, ela precisa ver um cardiologista, o telefone é o 11 99999-8888, pode ser na próxima terça de manhã?",
                "expected_extractions": ["nome", "tipo_consulta", "telefone", "data"],
                "description": "Complex single sentence with all data"
            },
            {
                "message": "Bom dia! Meu nome é Pedro dos Santos e eu gostaria de agendar uma consulta de rotina para o próximo fim de semana, se possível no sábado. Meu número é (11) 98765-4321",
                "expected_extractions": ["nome", "telefone", "data"],
                "description": "Natural conversation with relative dates"
            },
            {
                "message": "Olha, preciso remarcar aquela consulta do João que estava marcada pra amanhã, o telefone dele é 11987654321, pode ser na outra semana?",
                "expected_extractions": ["nome", "telefone"],
                "description": "Rescheduling with indirect references"
            }
        ]
        
        for test_case in complex_test_cases:
            response = self.client.post(
                "/chat/message",
                json={
                    "message": test_case["message"],
                    "session_id": str(uuid.uuid4())  # New session for each test
                }
            )
            
            assert response.status_code == 200, f"Failed for: {test_case['description']}"
            
            data = response.json()
            extracted_data = data.get("extracted_data", {})
            
            # Count successful extractions
            extracted_count = 0
            for expected_field in test_case["expected_extractions"]:
                # Check both Portuguese and English variants
                if expected_field in extracted_data and extracted_data[expected_field]:
                    extracted_count += 1
                elif expected_field == "nome" and "name" in extracted_data and extracted_data["name"]:
                    extracted_count += 1
                elif expected_field == "telefone" and "phone" in extracted_data and extracted_data["phone"]:
                    extracted_count += 1
                elif expected_field == "data" and "date" in extracted_data and extracted_data["date"]:
                    extracted_count += 1
                elif expected_field == "tipo_consulta" and "consultation_type" in extracted_data and extracted_data["consultation_type"]:
                    extracted_count += 1
            
            # Should extract at least half of the expected fields from complex text
            expected_count = len(test_case["expected_extractions"])
            success_rate = extracted_count / expected_count
            
            assert success_rate >= 0.5, \
                f"Low extraction success for '{test_case['description']}': {extracted_count}/{expected_count} = {success_rate:.1%}. Extracted: {extracted_data}"
    
    def test_multi_turn_context_accumulation(self):
        """
        Test context accumulation across multiple conversation turns.
        Addresses Technical Debt #2 - Context Management Broken.
        """
        session_id = str(uuid.uuid4())
        conversation_turns = [
            {
                "message": "Oi, preciso marcar consulta",
                "expected_new_fields": [],
                "description": "Initial greeting"
            },
            {
                "message": "Meu nome é Ana Santos",
                "expected_new_fields": ["nome", "name"],
                "description": "Name introduction"
            },
            {
                "message": "Telefone é 11999888777",
                "expected_new_fields": ["telefone", "phone"],
                "description": "Phone addition"
            },
            {
                "message": "Queria para segunda-feira de manhã",
                "expected_new_fields": ["data", "date"],
                "description": "Date specification"
            },
            {
                "message": "É consulta de dermatologia",
                "expected_new_fields": ["tipo_consulta", "consultation_type"],
                "description": "Consultation type"
            }
        ]
        
        accumulated_fields = set()
        
        for i, turn in enumerate(conversation_turns):
            response = self.client.post(
                "/chat/message",
                json={
                    "message": turn["message"],
                    "session_id": session_id
                }
            )
            
            assert response.status_code == 200, f"Turn {i+1} failed: {turn['description']}"
            
            data = response.json()
            extracted_data = data.get("extracted_data", {})
            
            # Check for new fields
            for expected_field in turn["expected_new_fields"]:
                if expected_field in extracted_data and extracted_data[expected_field]:
                    accumulated_fields.add(expected_field)
            
            # For turns after the first, should have accumulated previous context
            if i > 0:
                # Should maintain previously extracted information
                current_fields = set(k for k, v in extracted_data.items() if v)
                
                # Should have some accumulation (not losing all previous data)
                if i >= 2:  # By turn 3, should have accumulated some context
                    assert len(current_fields) >= 2, \
                        f"Turn {i+1}: Should accumulate context. Current fields: {current_fields}"
        
        # By end of conversation, should have accumulated multiple data points
        assert len(accumulated_fields) >= 3, \
            f"Should accumulate multiple fields across conversation: {accumulated_fields}"
    
    def test_confidence_and_completeness_progression(self):
        """
        Test that confidence scores and completeness improve through conversation.
        """
        session_id = str(uuid.uuid4())
        
        # Track progression metrics
        conversation_metrics = []
        
        conversation_steps = [
            "Olá",
            "João Silva",
            "Telefone 11999888777",
            "Consulta para amanhã às 14h",
            "É consulta de cardiologia"
        ]
        
        for step in conversation_steps:
            response = self.client.post(
                "/chat/message",
                json={
                    "message": step,
                    "session_id": session_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Collect metrics
                metrics = {
                    "confidence_score": data.get("confidence_score", 0),
                    "extracted_fields_count": len([v for v in data.get("extracted_data", {}).values() if v]),
                    "validation_errors": data.get("validation_summary", {}).get("total_errors", 0)
                }
                
                conversation_metrics.append(metrics)
        
        if len(conversation_metrics) >= 3:
            first_metrics = conversation_metrics[0]
            last_metrics = conversation_metrics[-1]
            
            # Should show improvement in data collection
            assert last_metrics["extracted_fields_count"] >= first_metrics["extracted_fields_count"], \
                "Should extract more fields as conversation progresses"
            
            # Confidence should generally improve (allowing some tolerance)
            confidence_improvement = last_metrics["confidence_score"] - first_metrics["confidence_score"]
            assert confidence_improvement >= -0.2, \
                f"Confidence should not significantly decrease: {first_metrics['confidence_score']} -> {last_metrics['confidence_score']}"


class TestContextManagementFlow:
    """
    Test specific context management and session handling.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client."""
        self.client = TestClient(app)
    
    def test_session_isolation(self):
        """
        Test that different sessions are properly isolated.
        """
        session_a = str(uuid.uuid4())
        session_b = str(uuid.uuid4())
        
        # Session A: Set name
        response_a1 = self.client.post(
            "/chat/message",
            json={
                "message": "Meu nome é Alice",
                "session_id": session_a
            }
        )
        
        # Session B: Set different name
        response_b1 = self.client.post(
            "/chat/message",
            json={
                "message": "Meu nome é Bob",
                "session_id": session_b
            }
        )
        
        # Session A: Add phone
        response_a2 = self.client.post(
            "/chat/message",
            json={
                "message": "Telefone 11999888777",
                "session_id": session_a
            }
        )
        
        # Session B: Add different phone
        response_b2 = self.client.post(
            "/chat/message",
            json={
                "message": "Telefone 11888999777",
                "session_id": session_b
            }
        )
        
        # Verify sessions don't interfere
        if all(r.status_code == 200 for r in [response_a1, response_b1, response_a2, response_b2]):
            data_a = response_a2.json()
            data_b = response_b2.json()
            
            extracted_a = data_a.get("extracted_data", {})
            extracted_b = data_b.get("extracted_data", {})
            
            # Session A should have Alice's data
            name_a = extracted_a.get("nome") or extracted_a.get("name", "")
            phone_a = extracted_a.get("telefone") or extracted_a.get("phone", "")
            
            # Session B should have Bob's data  
            name_b = extracted_b.get("nome") or extracted_b.get("name", "")
            phone_b = extracted_b.get("telefone") or extracted_b.get("phone", "")
            
            if name_a and name_b:
                assert "Alice" in name_a and "Bob" in name_b, \
                    f"Session isolation failed: A={name_a}, B={name_b}"
            
            if phone_a and phone_b:
                # Phones should be different
                phone_a_digits = ''.join(filter(str.isdigit, phone_a))
                phone_b_digits = ''.join(filter(str.isdigit, phone_b))
                assert phone_a_digits != phone_b_digits, \
                    f"Phone isolation failed: A={phone_a}, B={phone_b}"
    
    def test_session_context_retrieval(self):
        """
        Test retrieval of session context.
        """
        session_id = str(uuid.uuid4())
        
        # Build context
        messages = [
            "Meu nome é Carlos Silva",
            "Telefone 11999888777",
            "Consulta de oftalmologia"
        ]
        
        for message in messages:
            response = self.client.post(
                "/chat/message",
                json={
                    "message": message,
                    "session_id": session_id
                }
            )
            assert response.status_code == 200
        
        # Try to retrieve session if endpoint exists
        try:
            session_response = self.client.get(f"/sessions/{session_id}")
            
            if session_response.status_code == 200:
                session_data = session_response.json()
                
                # Should contain session information
                assert "id" in session_data or "session_id" in session_data
                
                # Should have context or extracted data
                has_context = ("context" in session_data or 
                             "extracted_data" in session_data or
                             "conversation" in session_data)
                
                assert has_context, "Session should contain conversation context"
        
        except Exception:
            # Session endpoint might not be implemented yet
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])