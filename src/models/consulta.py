"""
SQLAlchemy model for Consulta (medical appointment) entity.

This model represents medical appointments with extracted data from natural language conversations.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.core.database import Base


class Consulta(Base):
    """
    Model for medical appointment data extracted from conversations.
    
    Fields:
        id: Primary key (SERIAL)
        nome: Patient name
        telefone: Phone number
        data: Appointment date
        horario: Appointment time
        tipo_consulta: Type of consultation
        observacoes: Additional notes
        status: Appointment status
        confidence_score: Extraction confidence (0.0-1.0)
        session_id: Chat session UUID
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """
    
    __tablename__ = "consultas"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Patient information
    nome = Column(String(255), nullable=False, index=True)
    telefone = Column(String(20), nullable=True, index=True)
    
    # Appointment details
    data = Column(DateTime, nullable=True, index=True)
    horario = Column(String(10), nullable=True)  # Format: "HH:MM"
    tipo_consulta = Column(String(100), nullable=True, index=True)
    observacoes = Column(Text, nullable=True)
    
    # Status and metadata
    status = Column(String(50), default="pendente", index=True)
    confidence_score = Column(DECIMAL(3, 2), nullable=True)  # 0.00 to 1.00
    
    # Session tracking
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        """String representation of the Consulta model."""
        return f"<Consulta(id={self.id}, nome='{self.nome}', data={self.data}, status='{self.status}')>"
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'nome': self.nome,
            'telefone': self.telefone,
            'data': self.data.isoformat() if self.data else None,
            'horario': self.horario,
            'tipo_consulta': self.tipo_consulta,
            'observacoes': self.observacoes,
            'status': self.status,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None,
            'session_id': str(self.session_id) if self.session_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 