"""
Main entry point for the Data Structuring Agent.

This module provides CLI commands for testing and development.
"""

import sys
import json
import logging
from typing import Optional

from .core.config import get_settings
from .core.logging import setup_logging
from .core.entity_extraction import EntityExtractor
from .core.validators import validate_brazilian_phone, parse_relative_date, normalize_name, calculate_validation_confidence
from .core.data_normalizer import normalize_consulta_data
from .core.reasoning_engine import ReasoningEngine
from .core.database import create_tables, test_connection, get_engine

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def test_entity_extraction(text: str) -> None:
    """Test entity extraction from natural language text."""
    try:
        extractor = EntityExtractor()
        result = extractor.extract_entities(text)
        
        print("=== Entity Extraction Test ===")
        print(f"Input: {text}")
        print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        logger.error(f"Entity extraction test failed: {e}")
        print(f"Error: {e}")


def test_validation(data_json: str) -> None:
    """Test data validation and normalization."""
    try:
        # Parse JSON input
        data = json.loads(data_json)
        
        # Validate and normalize data
        validation_result = {}
        normalized_data = normalize_consulta_data(data)
        
        # Test phone validation if present
        if 'phone' in data and data['phone']:
            validation_result['phone'] = validate_brazilian_phone(str(data['phone']))
        
        # Test date parsing if present
        if 'date' in data and data['date']:
            validation_result['date'] = parse_relative_date(str(data['date']))
        
        # Test name normalization if present
        if 'name' in data and data['name']:
            validation_result['name'] = normalize_name(str(data['name']))
        
        # Calculate confidence
        validation_result['confidence'] = calculate_validation_confidence(data)
        
        print("=== Data Validation & Normalization Test ===")
        print(f"Input: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print(f"Validation: {json.dumps(validation_result, indent=2, ensure_ascii=False)}")
        print(f"Normalized: {json.dumps(normalized_data, indent=2, ensure_ascii=False)}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON input: {e}")
        print(f"Error: Invalid JSON - {e}")
    except Exception as e:
        logger.error(f"Validation test failed: {e}")
        print(f"Error: {e}")


def test_reasoning(text: str) -> None:
    """Test reasoning engine with partial information."""
    try:
        reasoning_engine = ReasoningEngine()
        result = reasoning_engine.process_message(text)
        
        print("=== Reasoning Engine Test ===")
        print(f"Input: {text}")
        print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        logger.error(f"Reasoning test failed: {e}")
        print(f"Error: {e}")


def test_database() -> None:
    """Test database connection and table creation."""
    try:
        print("=== Database Connection Test ===")
        
        # Test connection
        if test_connection():
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")
            return
        
        # Test table creation
        if create_tables():
            print("✅ Database tables created successfully")
        else:
            print("❌ Database table creation failed")
            
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        print(f"Error: {e}")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m src.main extract <text>")
        print("  python -m src.main validate <json_data>")
        print("  python -m src.main reason <text>")
        print("  python -m src.main setup-db")
        return
    
    command = sys.argv[1]
    
    try:
        if command == "extract":
            if len(sys.argv) < 3:
                print("Error: Text required for extraction")
                return
            text = sys.argv[2]
            test_entity_extraction(text)
            
        elif command == "validate":
            if len(sys.argv) < 3:
                print("Error: JSON data required for validation")
                return
            data_json = sys.argv[2]
            test_validation(data_json)
            
        elif command == "reason":
            if len(sys.argv) < 3:
                print("Error: Text required for reasoning")
                return
            text = sys.argv[2]
            test_reasoning(text)
            
        elif command == "setup-db":
            test_database()
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands: extract, validate, reason, setup-db")
            
    except Exception as e:
        logger.error(f"CLI execution failed: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()