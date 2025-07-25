"""
Main entry point for the Data Structuring Agent.

This module provides CLI commands for testing and development.
"""

import sys
import json
import logging
from typing import Optional, List

from .core.config import get_settings
from .core.logging.logger_factory import get_logger
from .core.entity_extraction import EntityExtractor
from .core.validation.normalizers.data_normalizer import DataNormalizer
from .core.reasoning.reasoning_coordinator import ReasoningCoordinator
from .core.database import create_tables, test_connection, get_engine
from .services.consultation_service import ConsultationService
from sqlalchemy import text
import asyncio

# Setup logging
# setup_logging() # This line is removed as per the edit hint.
logger = get_logger(__name__)


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
        
        # Initialize DataNormalizer
        normalizer = DataNormalizer()
        
        # Normalize consultation data using new system
        normalized_data = normalizer.normalize_consultation_data(data)
        
        # Get validation results from the normalized data
        validation_result = {
            'success': normalized_data.get('success', False),
            'confidence': normalized_data.get('confidence', 0.0),
            'errors': normalized_data.get('errors', [])
        }
        
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
        reasoning_engine = ReasoningCoordinator()
        result = reasoning_engine.process_message(text)
        
        print("=== Reasoning Engine Test ===")
        print(f"Input: {text}")
        print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        logger.error(f"Reasoning test failed: {e}")
        print(f"Error: {e}")


async def test_persist(message: str, session_id: Optional[str] = None) -> None:
    """Test consultation processing and persistence."""
    try:
        print("=== Consultation Processing & Persistence Test ===")
        
        service = ConsultationService()
        result = await service.process_and_persist(message, session_id)
        
        print(f"Input message: {message}")
        print(f"Session ID: {session_id or 'None'}")
        print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result["success"]:
            print(f"✅ Consultation created successfully with ID: {result['consultation_id']}")
            print(f"📊 Confidence score: {result['confidence']:.2f}")
            if result.get("errors"):
                print(f"⚠️  Validation warnings: {result['errors']}")
        else:
            print(f"❌ Processing failed: {result.get('errors', ['Unknown error'])}")
            
    except Exception as e:
        logger.error(f"Persistence test failed: {e}")
        print(f"Error: {e}")


async def test_chat_conversation(messages: List[str], session_id: Optional[str] = None) -> None:
    """Test complete chat conversation with persistence integration."""
    try:
        print("=== Complete Chat Conversation Test ===")
        print(f"Session ID: {session_id or 'Auto-generated'}")
        print(f"Messages to process: {len(messages)}")
        print()
        
        # Import here to avoid circular imports
        import requests
        import time
        
        settings = get_settings()
        base_url = settings.BASE_URL
        
        for i, message in enumerate(messages, 1):
            print(f"--- Message {i}/{len(messages)} ---")
            print(f"📤 Sending: {message}")
            
            # Prepare request
            payload = {"message": message}
            if session_id:
                payload["session_id"] = session_id
            
            try:
                # Send request to chat endpoint
                response = requests.post(
                    f"{base_url}/chat/message",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"📥 Response: {result['response']}")
                    print(f"🎯 Action: {result.get('action', 'N/A')}")
                    print(f"📊 Confidence: {result.get('confidence', 0.0):.2f}")
                    
                    if result.get('extracted_data'):
                        print(f"📋 Extracted Data: {list(result['extracted_data'].keys())}")
                    
                    if result.get('consultation_id'):
                        print(f"💾 Persisted Consultation ID: {result['consultation_id']}")
                        print(f"💾 Persistence Status: {result.get('persistence_status', 'N/A')}")
                    
                    if result.get('next_questions'):
                        print(f"❓ Next Questions: {result['next_questions']}")
                    
                    # Update session_id for next message (only if we got a valid response)
                    if result.get('session_id'):
                        session_id = result['session_id']
                    
                else:
                    print(f"❌ Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Network error: {e}")
            
            print()
            time.sleep(1)  # Small delay between messages
        
        # Show final session info
        print("--- Session Summary ---")
        try:
            session_response = requests.get(f"{base_url}/sessions/{session_id}")
            if session_response.status_code == 200:
                session_info = session_response.json()
                print(f"📊 Total Messages: {session_info.get('total_messages', 0)}")
                print(f"📋 Extracted Fields: {session_info.get('extracted_fields', [])}")
                print(f"📈 Data Completeness: {session_info.get('data_completeness', 0.0):.2f}")
            else:
                print(f"❌ Could not get session info: {session_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error getting session info: {e}")
        
        # Show persisted consultations
        print("\n--- Persisted Consultations ---")
        try:
            consultations_response = requests.get(f"{base_url}/consultations")
            if consultations_response.status_code == 200:
                consultations_data = consultations_response.json()
                consultations = consultations_data.get('consultations', [])
                print(f"📊 Total Consultations: {len(consultations)}")
                
                for consultation in consultations[:5]:  # Show first 5
                    print(f"   - ID: {consultation.get('id')}, Nome: {consultation.get('nome', 'N/A')}, Status: {consultation.get('status', 'N/A')}")
                
                if len(consultations) > 5:
                    print(f"   ... and {len(consultations) - 5} more")
            else:
                print(f"❌ Could not get consultations: {consultations_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error getting consultations: {e}")
            
    except Exception as e:
        logger.error(f"Chat conversation test failed: {e}")
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
        print("  python -m src.main persist <message> [session_id]")
        print("  python -m src.main chat <message1> <message2> ... [session_id]")
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
            
        elif command == "persist":
            if len(sys.argv) < 3:
                print("Error: Message required for persistence")
                return
            message = sys.argv[2]
            session_id = sys.argv[3] if len(sys.argv) > 3 else None
            asyncio.run(test_persist(message, session_id))
            
        elif command == "chat":
            if len(sys.argv) < 3:
                print("Error: At least one message required for chat conversation")
                return
            # Parse messages and session_id correctly
            if len(sys.argv) > 3:
                # Check if last argument looks like a session_id (UUID format)
                last_arg = sys.argv[-1]
                if len(last_arg) == 36 and '-' in last_arg:  # UUID format
                    messages = sys.argv[2:-1]
                    session_id = last_arg
                else:
                    messages = sys.argv[2:]
                    session_id = None
            else:
                messages = [sys.argv[2]]
                session_id = None
            asyncio.run(test_chat_conversation(messages, session_id))
            
        elif command == "setup-db":
            test_database()
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands: extract, validate, reason, persist, chat, setup-db")
            
    except Exception as e:
        logger.error(f"CLI execution failed: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()