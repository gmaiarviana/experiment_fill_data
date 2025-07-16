"""
SQLAlchemy model for ChatSession entity.

This model represents chat sessions with context management and user tracking.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from src.core.database import Base


class ChatSession(Base):
    """
    Model for chat session management and context tracking.
    
    Fields:
        id: Primary key (SERIAL)
        user_id: User identifier (can be anonymous)
        context: JSONB field for session context and memory
        last_activity: Last activity timestamp
        status: Session status (active, closed, expired)
    """
    
    __tablename__ = "chat_sessions"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User identification
    user_id = Column(String(255), nullable=True, index=True)  # Can be anonymous
    
    # Session context and memory (JSONB for PostgreSQL)
    context = Column(JSONB, nullable=True, default=dict)
    
    # Session management
    last_activity = Column(DateTime, default=func.now(), nullable=False, index=True)
    status = Column(String(50), default="active", index=True)  # active, closed, expired
    
    def __repr__(self):
        """String representation of the ChatSession model."""
        return f"<ChatSession(id={self.id}, user_id='{self.user_id}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'context': self.context,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'status': self.status
        }
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = func.now()
    
    def close_session(self):
        """Mark session as closed."""
        self.status = "closed"
        self.update_activity()
    
    def expire_session(self):
        """Mark session as expired."""
        self.status = "expired"
        self.update_activity()
    
    def is_active(self):
        """Check if session is active."""
        return self.status == "active" 