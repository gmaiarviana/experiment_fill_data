"""
Fixtures for conversation testing scenarios.
"""

from typing import List, Dict, Any


class ConversationScenarios:
    """
    Predefined conversation scenarios for testing user journeys.
    """
    
    COMPLETE_BOOKING_SUCCESS = {
        "name": "Complete Booking Success",
        "description": "User provides all information progressively and books successfully",
        "messages": [
            {
                "message": "Olá, preciso marcar uma consulta",
                "expected_extractions": [],
                "expected_response_type": "greeting_ask_details"
            },
            {
                "message": "Meu nome é João Silva",
                "expected_extractions": ["nome", "name"],
                "expected_response_type": "ask_more_details"
            },
            {
                "message": "Telefone é 11999888777",
                "expected_extractions": ["telefone", "phone"],
                "expected_response_type": "ask_more_details"
            },
            {
                "message": "Para amanhã às 14h",
                "expected_extractions": ["data", "date", "horario", "time"],
                "expected_response_type": "ask_consultation_type_or_confirm"
            },
            {
                "message": "Consulta de cardiologia",
                "expected_extractions": ["tipo_consulta", "consultation_type"],
                "expected_response_type": "confirmation_or_creation"
            }
        ],
        "expected_final_state": "consultation_ready_or_created",
        "min_confidence_final": 0.8
    }
    
    CORRECTION_FLOW = {
        "name": "User Correction Flow", 
        "description": "User corrects previously provided information",
        "messages": [
            {
                "message": "João Silva, telefone 11999888777",
                "expected_extractions": ["nome", "telefone"],
                "validation_note": "Initial data extraction"
            },
            {
                "message": "Na verdade, o telefone correto é 11888999777",
                "expected_extractions": ["telefone"],
                "validation_note": "Should update phone, keep name",
                "expected_phone_contains": "11888999777"
            }
        ],
        "expected_final_state": "corrected_data",
        "validation_rules": [
            "Phone should be updated to corrected value",
            "Name should be preserved from first message"
        ]
    }
    
    COMPLEX_SINGLE_MESSAGE = {
        "name": "Complex Single Message",
        "description": "User provides most/all information in a single complex message",
        "messages": [
            {
                "message": "Oi, é para minha mãe Maria Santos, telefone 21987654321, consulta de cardiologia para próxima segunda às 10h da manhã",
                "expected_extractions": ["nome", "telefone", "tipo_consulta", "data", "horario"],
                "min_extractions": 4,
                "validation_rules": [
                    "Name should contain 'Maria Santos'",
                    "Phone should contain '21987654321'",
                    "Consultation type should be 'cardiologia'",
                    "Should extract future date",
                    "Should extract morning time (~10h)"
                ]
            }
        ],
        "expected_final_state": "near_complete_data",
        "min_confidence_final": 0.7
    }
    
    INVALID_DATA_RECOVERY = {
        "name": "Invalid Data Recovery",
        "description": "User provides invalid data, system helps correct it",
        "messages": [
            {
                "message": "João Silva, telefone 123",
                "expected_extractions": ["nome"],
                "validation_expectation": "phone_validation_error",
                "expected_response_contains": ["telefone", "phone", "número", "formato"]
            },
            {
                "message": "Desculpa, telefone correto é 11999888777",
                "expected_extractions": ["telefone"],
                "validation_expectation": "phone_validation_success",
                "expected_phone_format": "11999888777"
            }
        ],
        "expected_final_state": "valid_data_after_correction",
        "validation_rules": [
            "System should identify invalid phone in first message",
            "System should accept corrected phone in second message"
        ]
    }
    
    PAST_DATE_REJECTION = {
        "name": "Past Date Rejection",
        "description": "System rejects past dates and asks for future dates",
        "messages": [
            {
                "message": "João Silva, consulta para ontem",
                "expected_extractions": ["nome"],
                "validation_expectation": "date_validation_error",
                "expected_response_contains": ["data", "date", "futuro", "future", "passado"]
            },
            {
                "message": "Então pode ser para amanhã?",
                "expected_extractions": ["data"],
                "validation_expectation": "date_validation_success"
            }
        ],
        "expected_final_state": "valid_future_date",
        "business_rules": [
            "Past dates should be rejected",
            "Future dates should be accepted"
        ]
    }
    
    SESSION_ISOLATION = {
        "name": "Session Isolation Test",
        "description": "Multiple sessions should not interfere with each other",
        "sessions": [
            {
                "session_id": "session_a",
                "messages": [
                    "Meu nome é Alice",
                    "Telefone 11999888777"
                ],
                "expected_data": {
                    "nome_contains": "Alice",
                    "phone_contains": "11999888777"
                }
            },
            {
                "session_id": "session_b", 
                "messages": [
                    "Meu nome é Bob",
                    "Telefone 11888999777"
                ],
                "expected_data": {
                    "nome_contains": "Bob",
                    "phone_contains": "11888999777"
                }
            }
        ],
        "validation_rules": [
            "Session A should only contain Alice's data",
            "Session B should only contain Bob's data",
            "Sessions should not contaminate each other"
        ]
    }
    
    MULTI_TURN_CONTEXT_BUILD = {
        "name": "Multi-Turn Context Building",
        "description": "Context should accumulate across multiple conversation turns",
        "messages": [
            {
                "message": "Oi",
                "expected_extractions": [],
                "context_expectation": "greeting_response"
            },
            {
                "message": "João Silva",
                "expected_extractions": ["nome"],
                "context_expectation": "name_acknowledged"
            },
            {
                "message": "11999888777",
                "expected_extractions": ["telefone"],
                "context_expectation": "phone_added_to_existing_name"
            },
            {
                "message": "Amanhã de manhã",
                "expected_extractions": ["data"],
                "context_expectation": "date_added_to_existing_data"
            },
            {
                "message": "Cardiologia",
                "expected_extractions": ["tipo_consulta"],
                "context_expectation": "consultation_type_completes_data"
            }
        ],
        "progressive_validation": [
            "Turn 1: No data",
            "Turn 2: Has name only",
            "Turn 3: Has name + phone", 
            "Turn 4: Has name + phone + date",
            "Turn 5: Has complete data set"
        ],
        "expected_final_state": "complete_accumulated_context"
    }
    
    CONFIDENCE_PROGRESSION = {
        "name": "Confidence Score Progression",
        "description": "Confidence should improve as more valid data is collected",
        "messages": [
            {
                "message": "Oi",
                "expected_confidence_range": (0.0, 0.2),
                "data_completeness": "empty"
            },
            {
                "message": "João",
                "expected_confidence_range": (0.1, 0.4),
                "data_completeness": "partial_name"
            },
            {
                "message": "João Silva, telefone 11999888777",
                "expected_confidence_range": (0.4, 0.7),
                "data_completeness": "name_and_phone"
            },
            {
                "message": "Consulta de cardiologia para amanhã às 14h",
                "expected_confidence_range": (0.7, 1.0),
                "data_completeness": "near_complete"
            }
        ],
        "progression_rule": "confidence_should_generally_increase",
        "tolerance": 0.1  # Allow some decrease but not significant regression
    }


class ValidationTestCases:
    """
    Test cases focused on validation behavior.
    """
    
    BRAZILIAN_PHONE_VALIDATION = [
        {
            "input": "11999888777",
            "expected_valid": True,
            "format_expectation": "mobile_sp",
            "description": "São Paulo mobile number"
        },
        {
            "input": "(21) 3333-4444", 
            "expected_valid": True,
            "format_expectation": "landline_rj",
            "description": "Rio de Janeiro landline"
        },
        {
            "input": "123456",
            "expected_valid": False,
            "error_type": "too_short",
            "description": "Number too short"
        },
        {
            "input": "01999888777",
            "expected_valid": False,
            "error_type": "invalid_ddd",
            "description": "Invalid area code 01"
        }
    ]
    
    DATE_VALIDATION_BUSINESS_RULES = [
        {
            "input": "amanhã",
            "expected_valid": True,
            "business_rule": "future_dates_allowed",
            "description": "Tomorrow should be valid"
        },
        {
            "input": "próxima segunda",
            "expected_valid": True,
            "business_rule": "future_dates_allowed", 
            "description": "Next Monday should be valid"
        },
        {
            "input": "ontem",
            "expected_valid": False,
            "business_rule": "past_dates_rejected",
            "description": "Yesterday should be rejected"
        },
        {
            "input": "semana passada",
            "expected_valid": False,
            "business_rule": "past_dates_rejected",
            "description": "Past week should be rejected"
        }
    ]
    
    NAME_NORMALIZATION_CASES = [
        {
            "input": "joao silva",
            "expected_output": "Joao Silva",
            "normalization_rule": "title_case",
            "description": "Lowercase to title case"
        },
        {
            "input": "MARIA DA COSTA",
            "expected_output": "Maria da Costa", 
            "normalization_rule": "preposition_lowercase",
            "description": "Prepositions should be lowercase"
        },
        {
            "input": "pedro DE oliveira",
            "expected_output": "Pedro de Oliveira",
            "normalization_rule": "mixed_case_normalization",
            "description": "Mixed case with preposition"
        }
    ]


def get_scenario(scenario_name: str) -> Dict[str, Any]:
    """Get a specific conversation scenario by name."""
    scenarios = {
        "complete_booking": ConversationScenarios.COMPLETE_BOOKING_SUCCESS,
        "correction_flow": ConversationScenarios.CORRECTION_FLOW,
        "complex_single": ConversationScenarios.COMPLEX_SINGLE_MESSAGE,
        "invalid_recovery": ConversationScenarios.INVALID_DATA_RECOVERY,
        "past_date": ConversationScenarios.PAST_DATE_REJECTION,
        "session_isolation": ConversationScenarios.SESSION_ISOLATION,
        "context_build": ConversationScenarios.MULTI_TURN_CONTEXT_BUILD,
        "confidence_progression": ConversationScenarios.CONFIDENCE_PROGRESSION
    }
    
    return scenarios.get(scenario_name, {})


def get_validation_cases(case_type: str) -> List[Dict[str, Any]]:
    """Get validation test cases by type."""
    cases = {
        "phone": ValidationTestCases.BRAZILIAN_PHONE_VALIDATION,
        "date": ValidationTestCases.DATE_VALIDATION_BUSINESS_RULES,
        "name": ValidationTestCases.NAME_NORMALIZATION_CASES
    }
    
    return cases.get(case_type, [])