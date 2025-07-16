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
from sqlalchemy import text

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
        
        # Get expected tables from models
        from src.models import Consulta, ExtractionLog, ChatSession
        expected_tables = ['consultas', 'extraction_logs', 'chat_sessions']
        print(f"📋 Expected tables: {', '.join(expected_tables)}")
        
        # Check current tables before creation
        print("\n=== Checking Existing Tables ===")
        try:
            engine = get_engine()
            with engine.connect() as connection:
                result = connection.execute(text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                ))
                existing_tables = [row[0] for row in result.fetchall()]
                our_existing_tables = [table for table in existing_tables if table in expected_tables]
                
                print(f"📊 Existing tables in database: {len(existing_tables)} total")
                print(f"📊 Our tables already exist: {len(our_existing_tables)}/{len(expected_tables)}")
                
                if our_existing_tables:
                    print("✅ Existing tables:")
                    for table in our_existing_tables:
                        print(f"   - {table}")
                
                if len(our_existing_tables) == len(expected_tables):
                    print("🎉 All expected tables already exist!")
                    return
                    
        except Exception as e:
            logger.error(f"Failed to check existing tables: {e}")
            print(f"❌ Error checking existing tables: {e}")
        
        # Test table creation
        print("\n=== Creating Database Tables ===")
        try:
            if create_tables():
                print("✅ Database tables created successfully")
            else:
                print("❌ Database table creation failed")
                return
        except Exception as e:
            error_msg = str(e)
            if "permission denied" in error_msg.lower() or "insufficientprivilege" in error_msg.lower():
                print("❌ Permission denied: Cannot create tables")
                print("💡 This usually means:")
                print("   - Database user lacks CREATE privileges")
                print("   - Schema permissions are not set correctly")
                print("   - Try running as database owner or with elevated privileges")
                print(f"🔍 Error details: {error_msg}")
                return
            else:
                raise e
        
        # Verify tables were created
        print("\n=== Verifying Created Tables ===")
        try:
            engine = get_engine()
            with engine.connect() as connection:
                # Query to get all tables in public schema (PostgreSQL)
                result = connection.execute(text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                ))
                created_tables = [row[0] for row in result.fetchall()]
                
                # Filter to only our expected tables
                our_tables = [table for table in created_tables if table in expected_tables]
                
                print(f"📊 Tables found in database: {len(created_tables)} total")
                print(f"📊 Our tables created: {len(our_tables)}/{len(expected_tables)}")
                
                if our_tables:
                    print("✅ Created tables:")
                    for table in our_tables:
                        print(f"   - {table}")
                
                missing_tables = [table for table in expected_tables if table not in our_tables]
                if missing_tables:
                    print("❌ Missing tables:")
                    for table in missing_tables:
                        print(f"   - {table}")
                
                if len(our_tables) == len(expected_tables):
                    print("🎉 All expected tables created successfully!")
                else:
                    print("⚠️  Some tables may not have been created properly")
                    
        except Exception as e:
            logger.error(f"Failed to verify created tables: {e}")
            print(f"❌ Error verifying tables: {e}")
            
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        print(f"❌ Error: {e}")
        print("💡 Make sure PostgreSQL is running and accessible")
        print("💡 Check database permissions and user privileges")


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