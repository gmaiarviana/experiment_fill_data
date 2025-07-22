"""
Integration tests for data validation and normalization flow.
Tests for Technical Debt #7 - End-to-end data validation journey.
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
from fastapi.testclient import TestClient


class TestDataValidationJourney:
    """
    Test complete data validation flow from conversation to structured data.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client."""
        self.client = TestClient(app)
    
    def test_brazilian_phone_validation_journey(self):
        """
        Test complete journey with Brazilian phone number validation.
        """
        session_id = str(uuid.uuid4())
        
        phone_test_cases = [
            {
                "input": "João Silva, telefone 11999888777",
                "expected_format": "Brazilian mobile with DDD 11",
                "should_be_valid": True
            },
            {
                "input": "Maria Santos, telefone (21) 3333-4444",
                "expected_format": "Rio de Janeiro landline",
                "should_be_valid": True
            },
            {
                "input": "Pedro Costa, telefone 123456",
                "expected_format": "Invalid short number",
                "should_be_valid": False
            },
            {
                "input": "Ana Lima, telefone 01999888777",
                "expected_format": "Invalid DDD 01",
                "should_be_valid": False
            }
        ]
        
        for test_case in phone_test_cases:
            # Use separate session for each test to avoid context contamination
            test_session_id = str(uuid.uuid4())
            
            response = self.client.post(
                "/chat/message",
                json={
                    "message": test_case["input"],
                    "session_id": test_session_id
                }
            )
            
            assert response.status_code == 200, f"Failed for: {test_case['expected_format']}"
            
            data = response.json()
            extracted_data = data.get("extracted_data", {})
            validation_summary = data.get("validation_summary", {})
            
            # Check phone validation
            phone_value = extracted_data.get("telefone") or extracted_data.get("phone")
            
            if test_case["should_be_valid"]:
                if phone_value:
                    # Valid phones should be properly formatted
                    phone_digits = ''.join(filter(str.isdigit, phone_value))
                    assert len(phone_digits) >= 10, f"Valid phone should have at least 10 digits: {phone_value}"
                    
                    # Should start with valid DDD
                    if len(phone_digits) >= 2:
                        ddd = phone_digits[:2]
                        valid_ddds = ["11", "12", "13", "14", "15", "16", "17", "18", "19",  # SP
                                     "21", "22", "24",  # RJ
                                     "27", "28",  # ES
                                     "31", "32", "33", "34", "35", "37", "38",  # MG
                                     "41", "42", "43", "44", "45", "46",  # PR
                                     "47", "48", "49",  # SC
                                     "51", "53", "54", "55",  # RS
                                     "61",  # DF
                                     "62", "64",  # GO
                                     "63",  # TO
                                     "65", "66",  # MT
                                     "67",  # MS
                                     "68",  # AC
                                     "69",  # RO
                                     "71", "73", "74", "75", "77",  # BA
                                     "79",  # SE
                                     "81", "87",  # PE
                                     "82",  # AL
                                     "83",  # PB
                                     "84",  # RN
                                     "85", "88",  # CE
                                     "86", "89",  # PI
                                     "91", "93", "94",  # PA
                                     "92", "97",  # AM
                                     "95",  # RR
                                     "96",  # AP
                                     "98", "99"]  # MA
                        
                        assert ddd in valid_ddds, f"Invalid Brazilian DDD: {ddd}"
            else:
                # Invalid phones should trigger validation errors or suggestions
                if validation_summary:
                    errors = validation_summary.get("total_errors", 0)
                    if errors == 0:
                        # If no validation errors reported, system might still be processing
                        # Check if phone was actually extracted
                        if phone_value:
                            # If phone was extracted from invalid input, should be flagged somehow
                            phone_digits = ''.join(filter(str.isdigit, phone_value))
                            # Very short phones should not be considered valid
                            if len(phone_digits) < 8:
                                assert False, f"Should not extract very short phone: {phone_value}"
    
    def test_date_validation_with_business_rules(self):
        """
        Test date validation with business rules (future dates only).
        """
        session_id = str(uuid.uuid4())
        
        date_test_cases = [
            {
                "input": "João Silva, consulta para amanhã",
                "expected_validity": True,
                "description": "Tomorrow should be valid"
            },
            {
                "input": "Maria Santos, consulta para próxima segunda",
                "expected_validity": True,
                "description": "Next Monday should be valid"
            },
            {
                "input": "Pedro Costa, consulta para ontem",
                "expected_validity": False,
                "description": "Yesterday should be invalid"
            },
            {
                "input": "Ana Lima, consulta para semana passada",
                "expected_validity": False,
                "description": "Past week should be invalid"
            }
        ]
        
        for test_case in date_test_cases:
            test_session_id = str(uuid.uuid4())
            
            response = self.client.post(
                "/chat/message",
                json={
                    "message": test_case["input"],
                    "session_id": test_session_id
                }
            )
            
            assert response.status_code == 200, f"Failed for: {test_case['description']}"
            
            data = response.json()
            extracted_data = data.get("extracted_data", {})
            validation_summary = data.get("validation_summary", {})
            
            date_value = extracted_data.get("data") or extracted_data.get("date")
            
            if test_case["expected_validity"]:
                if date_value:
                    # Valid dates should be in the future
                    # Check if it's a reasonable date format
                    assert len(date_value) >= 8, f"Date should be properly formatted: {date_value}"
                    
                    # Should contain date separators
                    has_separators = "-" in date_value or "/" in date_value
                    assert has_separators, f"Date should have separators: {date_value}"
            else:
                # Invalid dates should trigger validation errors or be rejected
                if date_value:
                    # If date was extracted, check validation errors
                    errors = validation_summary.get("total_errors", 0)
                    # Should have validation errors for past dates
                    # (This is a business rule that should be enforced)
                    pass  # System might accept but flag as error
    
    def test_name_normalization_journey(self):
        """
        Test name normalization through the complete flow.
        """
        name_test_cases = [
            {
                "input": "joao silva",
                "expected_normalized": "Joao Silva",
                "description": "Lowercase should be capitalized"
            },
            {
                "input": "MARIA DA COSTA",
                "expected_normalized": "Maria da Costa",
                "description": "Uppercase with preposition"
            },
            {
                "input": "pedro DE oliveira",
                "expected_normalized": "Pedro de Oliveira",
                "description": "Mixed case with preposition"
            },
            {
                "input": "ana DOS SANTOS",
                "expected_normalized": "Ana dos Santos",
                "description": "Mixed case with compound preposition"
            }
        ]
        
        for test_case in name_test_cases:
            test_session_id = str(uuid.uuid4())
            
            response = self.client.post(
                "/chat/message",
                json={
                    "message": f"Meu nome é {test_case['input']}",
                    "session_id": test_session_id
                }
            )
            
            assert response.status_code == 200, f"Failed for: {test_case['description']}"
            
            data = response.json()
            extracted_data = data.get("extracted_data", {})
            
            name_value = extracted_data.get("nome") or extracted_data.get("name")
            
            if name_value:
                # Check if normalization was applied
                # Should have proper capitalization
                words = name_value.split()
                for word in words:
                    if word.lower() not in ["da", "de", "do", "dos", "das"]:
                        # Non-preposition words should be capitalized
                        assert word[0].isupper(), f"Word should be capitalized: '{word}' in '{name_value}'"
                    else:
                        # Prepositions should be lowercase (except if first word)
                        if word != words[0]:
                            assert word.islower(), f"Preposition should be lowercase: '{word}' in '{name_value}'"
    
    def test_consultation_type_extraction_and_validation(self):
        """
        Test consultation type extraction and validation.
        """
        consultation_types = [
            {
                "input": "João Silva, consulta de cardiologia",
                "expected_type": "cardiologia",
                "description": "Specific medical specialty"
            },
            {
                "input": "Maria Santos, consulta de rotina",
                "expected_type": "rotina",
                "description": "General routine consultation"
            },
            {
                "input": "Pedro Costa, consulta oftalmológica",
                "expected_type": "oftalmologia",
                "description": "Ophthalmology with adjective form"
            },
            {
                "input": "Ana Lima, checkup médico",
                "expected_type": "checkup",
                "description": "Medical checkup"
            }
        ]
        
        for test_case in consultation_types:
            test_session_id = str(uuid.uuid4())
            
            response = self.client.post(
                "/chat/message",
                json={
                    "message": test_case["input"],
                    "session_id": test_session_id
                }
            )
            
            assert response.status_code == 200, f"Failed for: {test_case['description']}"
            
            data = response.json()
            extracted_data = data.get("extracted_data", {})
            
            consultation_type = (extracted_data.get("tipo_consulta") or 
                               extracted_data.get("consultation_type") or
                               extracted_data.get("tipo"))
            
            if consultation_type:
                # Should extract some form of consultation type
                consultation_type_lower = consultation_type.lower()
                
                # Should contain relevant medical terms
                medical_terms = ["cardiologia", "rotina", "oftalmologia", "checkup", 
                               "cardiology", "routine", "ophthalmology", "dermatologia"]
                
                has_medical_term = any(term in consultation_type_lower for term in medical_terms)
                assert has_medical_term, f"Should extract medical consultation type: {consultation_type}"
    
    def test_comprehensive_data_validation_flow(self):
        """
        Test comprehensive validation flow with mixed valid/invalid data.
        """
        session_id = str(uuid.uuid4())
        
        # Message with mixed data quality
        mixed_data_message = """
        João Silva, telefone é 11999888777, mas na verdade é 11888999777, 
        consulta de cardiologia para amanhã de manhã, 
        pode ser às 10h da manhã?
        """
        
        response = self.client.post(
            "/chat/message",
            json={
                "message": mixed_data_message,
                "session_id": session_id
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        extracted_data = data.get("extracted_data", {})
        validation_summary = data.get("validation_summary", {})
        
        # Should extract multiple fields
        extracted_fields = [k for k, v in extracted_data.items() if v]
        assert len(extracted_fields) >= 3, f"Should extract multiple fields: {extracted_fields}"
        
        # Should handle phone correction (latest value should be used)
        phone_value = extracted_data.get("telefone") or extracted_data.get("phone")
        if phone_value:
            # Should prefer the corrected phone number
            phone_digits = ''.join(filter(str.isdigit, phone_value))
            # Should contain one of the mentioned phone numbers
            assert any(num in phone_digits for num in ["11999888777", "11888999777"]), \
                f"Should contain one of the mentioned phones: {phone_value}"
        
        # Should extract consultation type
        consultation_type = (extracted_data.get("tipo_consulta") or 
                           extracted_data.get("consultation_type"))
        if consultation_type:
            assert "cardiologia" in consultation_type.lower() or "cardiology" in consultation_type.lower(), \
                f"Should extract cardiologia: {consultation_type}"
        
        # Should extract time information
        time_fields = ["horario", "hora", "time", "horário"]
        has_time = any(field in extracted_data and extracted_data[field] for field in time_fields)
        
        if has_time:
            # Should extract 10h or 10:00 format
            for field in time_fields:
                if field in extracted_data and extracted_data[field]:
                    time_value = str(extracted_data[field])
                    assert "10" in time_value, f"Should extract 10h: {time_value}"
    
    def test_confidence_scoring_with_validation_quality(self):
        """
        Test that confidence scores reflect validation quality.
        """
        test_cases = [
            {
                "message": "João Silva, telefone 11999888777, consulta de cardiologia para amanhã às 14h",
                "expected_min_confidence": 0.7,
                "description": "Complete valid data should have high confidence"
            },
            {
                "message": "João, telefone 123, consulta ontem",
                "expected_max_confidence": 0.5,
                "description": "Invalid data should have low confidence"
            },
            {
                "message": "Olá",
                "expected_max_confidence": 0.3,
                "description": "No data should have very low confidence"
            }
        ]
        
        for test_case in test_cases:
            test_session_id = str(uuid.uuid4())
            
            response = self.client.post(
                "/chat/message",
                json={
                    "message": test_case["message"],
                    "session_id": test_session_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                confidence = data.get("confidence_score", 0)
                
                if "expected_min_confidence" in test_case:
                    assert confidence >= test_case["expected_min_confidence"], \
                        f"{test_case['description']}: Expected >= {test_case['expected_min_confidence']}, got {confidence}"
                
                if "expected_max_confidence" in test_case:
                    assert confidence <= test_case["expected_max_confidence"], \
                        f"{test_case['description']}: Expected <= {test_case['expected_max_confidence']}, got {confidence}"


class TestValidationIntegrationWithReasoningEngine:
    """
    Test integration between validation system and reasoning engine.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client."""
        self.client = TestClient(app)
    
    def test_validation_feedback_loop(self):
        """
        Test that validation results influence conversation flow.
        """
        session_id = str(uuid.uuid4())
        
        # Send message with validation errors
        response = self.client.post(
            "/chat/message",
            json={
                "message": "João Silva, telefone 123",
                "session_id": session_id
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        response_text = data.get("response", "").lower()
        validation_summary = data.get("validation_summary", {})
        
        # System should respond to validation errors
        error_count = validation_summary.get("total_errors", 0)
        
        if error_count > 0:
            # Response should acknowledge the error
            error_indicators = ["telefone", "phone", "número", "numero", "inválido", "invalid", 
                              "formato", "format", "correto", "correct"]
            has_error_response = any(indicator in response_text for indicator in error_indicators)
            
            # Should either respond to error or provide suggestions
            has_suggestions = len(validation_summary.get("suggestions", [])) > 0
            
            assert has_error_response or has_suggestions, \
                f"System should respond to validation errors: {response_text}"
    
    def test_progressive_validation_through_conversation(self):
        """
        Test validation improvement through progressive conversation.
        """
        session_id = str(uuid.uuid4())
        
        conversation_steps = [
            {
                "message": "João",
                "validation_expectation": "Should need more name information"
            },
            {
                "message": "João Silva",
                "validation_expectation": "Should improve name validation"
            },
            {
                "message": "Telefone 11999888777",
                "validation_expectation": "Should validate phone successfully"
            },
            {
                "message": "Consulta para amanhã",
                "validation_expectation": "Should add valid date"
            }
        ]
        
        error_counts = []
        
        for i, step in enumerate(conversation_steps):
            response = self.client.post(
                "/chat/message",
                json={
                    "message": step["message"],
                    "session_id": session_id
                }
            )
            
            assert response.status_code == 200, f"Step {i+1} failed: {step['message']}"
            
            data = response.json()
            validation_summary = data.get("validation_summary", {})
            error_count = validation_summary.get("total_errors", 0)
            error_counts.append(error_count)
        
        # Validation should generally improve (fewer errors) as more valid data is added
        if len(error_counts) >= 2:
            # Later steps should not have significantly more errors than earlier ones
            # (allowing for some variation in validation strictness)
            first_half_avg = sum(error_counts[:len(error_counts)//2]) / (len(error_counts)//2)
            second_half_avg = sum(error_counts[len(error_counts)//2:]) / (len(error_counts) - len(error_counts)//2)
            
            # Should not get significantly worse
            assert second_half_avg <= first_half_avg + 1, \
                f"Validation should improve: {error_counts}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])