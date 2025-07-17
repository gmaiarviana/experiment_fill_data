"""
Consultation Service for orchestrating entity extraction, validation, and persistence.

This service coordinates the complete flow from natural language message
to persisted consultation record with proper error handling and logging.
"""

from src.repositories.consulta_repository import ConsultaRepository
from src.core.entity_extraction import EntityExtractor
from src.core.data_normalizer import normalize_consulta_data
from src.core.database import get_session_factory
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConsultationService:
    """
    Service for managing consultation data processing and persistence.
    
    Orchestrates the complete flow from natural language message to
    persisted consultation record, including entity extraction,
    data normalization, validation, and database persistence.
    """
    
    def __init__(self):
        """
        Initialize the ConsultationService with required components.
        """
        self.entity_extractor = EntityExtractor()
        self.session_factory = get_session_factory()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self.logger.info("ConsultationService initialized successfully")
    
    async def process_and_persist(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a natural language message and persist consultation data.
        
        This method orchestrates the complete flow:
        1. Extract entities from the message
        2. Normalize and validate the extracted data
        3. Persist the consultation record
        4. Return comprehensive result with metadata
        
        Args:
            message: Natural language message containing consultation information
            session_id: Optional session ID for tracking (converted to UUID if string)
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating if the operation was successful
            - consultation_id: ID of the created consultation record (if successful)
            - data: Extracted and normalized data
            - confidence: Confidence score from extraction and validation
            - errors: List of errors encountered (if any)
            - metadata: Additional processing metadata
        """
        start_time = datetime.now()
        self.logger.info(f"Starting consultation processing for message: {message[:100]}...")
        
        try:
            # Convert session_id to UUID if provided as string
            session_uuid = None
            if session_id:
                try:
                    session_uuid = uuid.UUID(session_id) if isinstance(session_id, str) else session_id
                    self.logger.debug(f"Using session ID: {session_uuid}")
                except ValueError as e:
                    self.logger.warning(f"Invalid session ID format: {session_id}, error: {e}")
                    session_uuid = None
            
            # Step 1: Extract entities from message
            self.logger.debug("Step 1: Extracting entities from message")
            extraction_result = await self.entity_extractor.extract_consulta_entities(message)
            
            if not extraction_result.get("success", False):
                error_msg = f"Entity extraction failed: {extraction_result.get('error', 'Unknown error')}"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "consultation_id": None,
                    "data": {},
                    "confidence": 0.0,
                    "errors": [error_msg],
                    "metadata": {
                        "processing_time": (datetime.now() - start_time).total_seconds(),
                        "step_failed": "entity_extraction",
                        "timestamp": datetime.now().isoformat()
                    }
                }
            
            extracted_data = extraction_result.get("extracted_data", {})
            confidence_score = extraction_result.get("confidence_score", 0.0)
            
            self.logger.info(f"Entity extraction successful. Confidence: {confidence_score}")
            self.logger.debug(f"Extracted data: {extracted_data}")
            
            # Step 2: Normalize and validate data
            self.logger.debug("Step 2: Normalizing and validating data")
            normalization_result = normalize_consulta_data(extracted_data)
            
            normalized_data = normalization_result.get("normalized_data", {})
            validation_errors = normalization_result.get("validation_errors", [])
            normalized_confidence = normalization_result.get("confidence_score", 0.0)
            
            # Use the higher confidence score between extraction and normalization
            final_confidence = max(confidence_score, normalized_confidence)
            
            self.logger.info(f"Data normalization completed. Confidence: {final_confidence}")
            if validation_errors:
                self.logger.warning(f"Validation errors found: {validation_errors}")
            
            # Step 3: Prepare data for persistence
            self.logger.debug("Step 3: Preparing data for persistence")
            
            # Map normalized data to model fields (accept both Portuguese and English field names)
            consulta_data = {
                "nome": normalized_data.get("name") or normalized_data.get("nome", ""),
                "telefone": normalized_data.get("phone") or normalized_data.get("telefone"),
                "data": normalized_data.get("consulta_date") or normalized_data.get("data"),
                "horario": normalized_data.get("horario"),
                "tipo_consulta": normalized_data.get("tipo_consulta"),
                "observacoes": normalized_data.get("observacoes"),
                "status": "pendente",  # Default status
                "confidence_score": final_confidence,
                "session_id": session_uuid
            }
            
            # Validate required fields
            if not consulta_data["nome"]:
                error_msg = "Nome do paciente é obrigatório"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "consultation_id": None,
                    "data": normalized_data,
                    "confidence": final_confidence,
                    "errors": [error_msg] + validation_errors,
                    "metadata": {
                        "processing_time": (datetime.now() - start_time).total_seconds(),
                        "step_failed": "validation",
                        "timestamp": datetime.now().isoformat()
                    }
                }
            
            # Step 4: Persist to database
            self.logger.debug("Step 4: Persisting consultation to database")
            
            with self.session_factory() as session:
                try:
                    repository = ConsultaRepository(session)
                    consulta = repository.create(consulta_data)
                    
                    # Commit the transaction
                    session.commit()
                    
                    self.logger.info(f"Consultation persisted successfully with ID: {consulta.id}")
                    
                    # Prepare success response
                    result = {
                        "success": True,
                        "consultation_id": consulta.id,
                        "data": consulta.to_dict(),
                        "confidence": final_confidence,
                        "errors": validation_errors,  # Include validation warnings
                        "metadata": {
                            "processing_time": (datetime.now() - start_time).total_seconds(),
                            "extraction_confidence": confidence_score,
                            "normalization_confidence": normalized_confidence,
                            "final_confidence": final_confidence,
                            "session_id": str(session_uuid) if session_uuid else None,
                            "timestamp": datetime.now().isoformat(),
                            "missing_fields": extraction_result.get("missing_fields", []),
                            "suggested_questions": extraction_result.get("suggested_questions", [])
                        }
                    }
                    
                    self.logger.info(f"Consultation processing completed successfully in {(datetime.now() - start_time).total_seconds():.2f}s")
                    return result
                    
                except Exception as e:
                    session.rollback()
                    error_msg = f"Database persistence failed: {str(e)}"
                    self.logger.error(error_msg, exc_info=True)
                    return {
                        "success": False,
                        "consultation_id": None,
                        "data": normalized_data,
                        "confidence": final_confidence,
                        "errors": [error_msg] + validation_errors,
                        "metadata": {
                            "processing_time": (datetime.now() - start_time).total_seconds(),
                            "step_failed": "persistence",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
        
        except Exception as e:
            error_msg = f"Unexpected error in consultation processing: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "consultation_id": None,
                "data": {},
                "confidence": 0.0,
                "errors": [error_msg],
                "metadata": {
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "step_failed": "unexpected_error",
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def get_consultation(self, id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a consultation by ID.
        
        Args:
            id: The consultation ID to retrieve
            
        Returns:
            Dictionary representation of the consultation or None if not found
        """
        self.logger.info(f"Retrieving consultation with ID: {id}")
        
        try:
            with self.session_factory() as session:
                repository = ConsultaRepository(session)
                consulta = repository.get(id)
                
                if consulta:
                    self.logger.info(f"Consultation {id} retrieved successfully")
                    return consulta.to_dict()
                else:
                    self.logger.warning(f"Consultation {id} not found")
                    return None
                    
        except Exception as e:
            error_msg = f"Error retrieving consultation {id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return None
    
    def list_consultations(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List consultations with pagination.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of consultation dictionaries
        """
        self.logger.info(f"Listing consultations (skip: {skip}, limit: {limit})")
        
        try:
            with self.session_factory() as session:
                repository = ConsultaRepository(session)
                consultas = repository.list(skip=skip, limit=limit)
                
                result = [consulta.to_dict() for consulta in consultas]
                self.logger.info(f"Retrieved {len(result)} consultations")
                return result
                
        except Exception as e:
            error_msg = f"Error listing consultations: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return []
    
    def get_consultations_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all consultations for a specific session.
        
        Args:
            session_id: The session ID to filter by
            
        Returns:
            List of consultation dictionaries for the session
        """
        self.logger.info(f"Retrieving consultations for session: {session_id}")
        
        try:
            session_uuid = uuid.UUID(session_id) if isinstance(session_id, str) else session_id
            
            with self.session_factory() as session:
                repository = ConsultaRepository(session)
                consultas = repository.find_by_session(session_uuid)
                
                result = [consulta.to_dict() for consulta in consultas]
                self.logger.info(f"Retrieved {len(result)} consultations for session {session_id}")
                return result
                
        except ValueError as e:
            error_msg = f"Invalid session ID format: {session_id}"
            self.logger.error(error_msg)
            return []
        except Exception as e:
            error_msg = f"Error retrieving consultations for session {session_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return []
    
    def update_consultation_status(self, id: int, new_status: str) -> Optional[Dict[str, Any]]:
        """
        Update the status of a consultation.
        
        Args:
            id: The consultation ID to update
            new_status: The new status to set
            
        Returns:
            Updated consultation dictionary or None if not found
        """
        self.logger.info(f"Updating consultation {id} status to: {new_status}")
        
        try:
            with self.session_factory() as session:
                repository = ConsultaRepository(session)
                consulta = repository.update_status(id, new_status)
                
                if consulta:
                    self.logger.info(f"Consultation {id} status updated successfully")
                    return consulta.to_dict()
                else:
                    self.logger.warning(f"Consultation {id} not found for status update")
                    return None
                    
        except Exception as e:
            error_msg = f"Error updating consultation {id} status: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return None 