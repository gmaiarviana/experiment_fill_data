"""
SQLAlchemy model for ExtractionLog entity.

This model represents logs of entity extraction operations for debugging and analysis.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from src.core.database import Base


class ExtractionLog(Base):
    """
    Model for logging entity extraction operations and reasoning steps.
    
    Fields:
        id: Primary key (SERIAL)
        session_id: Chat session UUID
        raw_message: Original user message
        extracted_data: JSONB field with extracted entities
        confidence_score: Extraction confidence (0.0-1.0)
        reasoning_steps: JSONB field with reasoning process steps
        created_at: Log creation timestamp
    """
    
    __tablename__ = "extraction_logs"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Session tracking
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Extraction data
    raw_message = Column(Text, nullable=False)
    extracted_data = Column(JSONB, nullable=True, default=dict)
    
    # Quality metrics
    confidence_score = Column(DECIMAL(3, 2), nullable=True)  # 0.00 to 1.00
    
    # Debugging and analysis
    reasoning_steps = Column(JSONB, nullable=True, default=list)
    
    # Timestamp
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        """String representation of the ExtractionLog model."""
        return f"<ExtractionLog(id={self.id}, session_id={self.session_id}, confidence={self.confidence_score})>"
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'session_id': str(self.session_id) if self.session_id else None,
            'raw_message': self.raw_message,
            'extracted_data': self.extracted_data,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None,
            'reasoning_steps': self.reasoning_steps,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def add_reasoning_step(self, step_type: str, description: str, data: dict = None):
        """
        Add a reasoning step to the log.
        
        Args:
            step_type: Type of reasoning step (think, extract, validate, act)
            description: Human-readable description
            data: Additional data for the step
        """
        if self.reasoning_steps is None:
            self.reasoning_steps = []
        
        step = {
            'type': step_type,
            'description': description,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data or {}
        }
        
        self.reasoning_steps.append(step) 