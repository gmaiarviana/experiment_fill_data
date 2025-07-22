"""
Chat Service for orchestrating conversation flow.

This service coordinates the complete conversation flow including:
- Message processing and routing
- Context management
- Response generation
- Integration with other services
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging
from src.core.container import get_openai_client, get_consultation_service
from src.core.reasoning.reasoning_coordinator import ReasoningCoordinator
from src.core.config import get_settings
from src.services.session_service import SessionService

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for orchestrating conversation flow and message processing.
    
    Coordinates the complete flow from user message to structured response,
    including context management, entity extraction, validation, and persistence.
    """
    
    def __init__(self):
        """Initialize ChatService with required dependencies."""
        self.session_service = SessionService()
        self.settings = get_settings()
        logger.info("ChatService initialized successfully")
    
    async def process_message(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message and return structured response.
        
        Args:
            message: User message to process
            session_id: Optional session ID for context continuity
            
        Returns:
            Dictionary containing complete response data
        """
        logger.info(f"Processing message: {message[:50]}...")
        
        try:
            # Get or create session context
            context = self._get_or_create_session_context(session_id)
            
            # Process message based on configuration
            if getattr(self.settings, "USE_FULL_LLM_VALIDATION", False):
                result = await self._process_with_full_llm(message, context)
            else:
                result = await self._process_with_reasoning_engine(message, context)
            
            # Update session context
            self.session_service.update_session(context["session_id"], context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._create_error_response(str(e), session_id)
    
    def _get_or_create_session_context(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get existing session context or create new one."""
        if not session_id:
            session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        context = self.session_service.get_session(session_id)
        if context is None:
            context = self.session_service.create_session(session_id, {
                "session_start": datetime.utcnow().isoformat(),
                "conversation_history": [],
                "extracted_data": {},
                "total_confidence": 0.0,
                "confidence_count": 0,
                "average_confidence": 0.0
            })
            logger.info(f"New session created: {session_id}")
        else:
            logger.info(f"Existing session retrieved: {session_id}")
        
        context["session_id"] = session_id
        return context
    
    async def _process_with_full_llm(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message using full LLM approach."""
        logger.info("[Feature Toggle] Using FULL_LLM_VALIDATION mode")
        
        openai_client = get_openai_client()
        if openai_client is None:
            return self._create_error_response("AI service unavailable", context["session_id"])
        
        try:
            # Get LLM response
            ai_response = await openai_client.full_llm_completion(message, context)
            
            # Parse LLM response
            llm_data = json.loads(ai_response) if isinstance(ai_response, str) else ai_response
            
            # Extract response components
            extracted_data = llm_data.get("extracted_data", {})
            confidence = llm_data.get("confidence", 0.0)
            action = llm_data.get("action", "extract")
            response_text = llm_data.get("response", "Desculpe, não consegui processar sua mensagem.")
            next_questions = llm_data.get("next_questions", [])
            validation_errors = llm_data.get("validation_errors", [])
            
            # Update context with extracted data
            self._update_context_with_data(context, extracted_data, confidence)
            
            # Add to conversation history
            context["conversation_history"].append({
                "user_message": message,
                "action": action,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "response": response_text,
                "session_id": context["session_id"],
                "timestamp": datetime.utcnow(),
                "action": action,
                "extracted_data": extracted_data,
                "confidence": confidence,
                "next_questions": next_questions,
                "consultation_id": None,
                "persistence_status": "not_applicable"
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM response: {e}")
            return self._create_error_response("Error processing AI response", context["session_id"])
    
    async def _process_with_reasoning_engine(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message using reasoning engine approach."""
        logger.info("Using ReasoningCoordinator mode")
        
        reasoning_engine = ReasoningCoordinator()
        if reasoning_engine is None:
            logger.warning("Reasoning Engine unavailable, using OpenAI fallback")
            return await self._process_with_openai_fallback(message, context)
        
        try:
            # Process with reasoning engine
            result = await reasoning_engine.process_message(message, context)
            
            # Extract result components
            action = result.get("action", "unknown")
            response_text = result.get("response", "Desculpe, não consegui processar sua mensagem.")
            extracted_data = result.get("extracted_data", {})
            confidence = result.get("confidence", 0.0)
            next_questions = result.get("next_questions", [])
            
            # Handle persistence if applicable
            consultation_id, persistence_status = await self._handle_persistence(
                message, context["session_id"], extracted_data, action
            )
            
            # Update response text with persistence info
            if persistence_status == "success":
                response_text = self._add_persistence_success_message(response_text, action, consultation_id)
            elif persistence_status == "failed":
                response_text = self._add_persistence_error_message(response_text, result.get("persistence_errors", []))
            
            return {
                "response": response_text,
                "session_id": context["session_id"],
                "timestamp": datetime.utcnow(),
                "action": action,
                "extracted_data": extracted_data,
                "confidence": confidence,
                "next_questions": next_questions,
                "consultation_id": consultation_id,
                "persistence_status": persistence_status
            }
            
        except Exception as e:
            logger.error(f"Error in reasoning engine: {e}")
            return await self._process_with_openai_fallback(message, context)
    
    async def _process_with_openai_fallback(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback processing using OpenAI directly."""
        openai_client = get_openai_client()
        if openai_client is None:
            return self._create_error_response("AI service unavailable", context["session_id"])
        
        ai_response = await openai_client.chat_completion(message)
        return {
            "response": ai_response,
            "session_id": context["session_id"],
            "timestamp": datetime.utcnow(),
            "action": "fallback",
            "extracted_data": {},
            "confidence": 0.0,
            "next_questions": [],
            "consultation_id": None,
            "persistence_status": "not_applicable"
        }
    
    async def _handle_persistence(self, message: str, session_id: str, extracted_data: Dict[str, Any], action: str) -> tuple:
        """Handle data persistence if applicable."""
        if not extracted_data or action not in ["extract", "confirm", "complete"]:
            return None, "not_applicable"
        
        consultation_service = get_consultation_service()
        if consultation_service is None:
            return None, "service_unavailable"
        
        try:
            persistence_result = await consultation_service.process_and_persist(
                message, 
                session_id,
                extracted_data.get("normalized_data", {})
            )
            
            if persistence_result.get("success", False):
                consultation_id = persistence_result.get("consultation_id")
                logger.info(f"✅ Consultation persisted successfully - ID: {consultation_id}")
                return consultation_id, "success"
            else:
                logger.warning(f"❌ Persistence failed: {persistence_result.get('errors', [])}")
                return None, "failed"
                
        except Exception as e:
            logger.error(f"Error during persistence: {e}")
            return None, "error"
    
    def _update_context_with_data(self, context: Dict[str, Any], extracted_data: Dict[str, Any], confidence: float) -> None:
        """Update session context with new extracted data and confidence metrics."""
        # Update extracted data
        if extracted_data:
            for key, value in extracted_data.items():
                if value is not None and value != "":
                    context["extracted_data"][key] = value
        
        # Update confidence metrics
        context["total_confidence"] += confidence
        context["confidence_count"] += 1
        context["average_confidence"] = context["total_confidence"] / context["confidence_count"]
    
    def _add_persistence_success_message(self, response_text: str, action: str, consultation_id: int) -> str:
        """Add persistence success message to response."""
        if action == "extract":
            return f"{response_text}\n\n✅ Consulta registrada com sucesso! (ID: {consultation_id})"
        elif action == "confirm":
            return f"{response_text}\n\n✅ Consulta confirmada e salva! (ID: {consultation_id})"
        elif action == "complete":
            return f"{response_text}\n\n✅ Consulta completa registrada com sucesso! (ID: {consultation_id})"
        return response_text
    
    def _add_persistence_error_message(self, response_text: str, errors: list) -> str:
        """Add persistence error message to response."""
        return f"{response_text}\n\n⚠️ Não foi possível salvar a consulta: {', '.join(errors)}"
    
    def _create_error_response(self, error_message: str, session_id: str) -> Dict[str, Any]:
        """Create error response structure."""
        return {
            "response": f"Ocorreu um erro ao processar sua mensagem: {error_message}",
            "session_id": session_id,
            "timestamp": datetime.utcnow(),
            "action": "error",
            "extracted_data": {},
            "confidence": 0.0,
            "next_questions": [],
            "consultation_id": None,
            "persistence_status": "error"
        } 