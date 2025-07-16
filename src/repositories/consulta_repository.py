from src.repositories.base_repository import BaseRepository
from src.models.consulta import Consulta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

class ConsultaRepository(BaseRepository[Consulta]):
    """
    Specialized repository for Consulta model operations.
    
    Extends BaseRepository with consulta-specific query methods and
    custom business logic for managing consultation records.
    """
    
    def __init__(self, session: Session):
        """
        Initialize the ConsultaRepository with a database session.
        
        Args:
            session: The database session instance
        """
        super().__init__(Consulta, session)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create(self, data: Dict[str, Any]) -> Consulta:
        """
        Create a new Consulta record with enhanced logging.
        
        Args:
            data: Dictionary containing the consulta data
            
        Returns:
            The created Consulta instance
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Call parent create method
            consulta = super().create(data)
            
            # Enhanced logging for consulta creation
            self.logger.info(
                f"Consulta created successfully - "
                f"ID: {consulta.id}, "
                f"Session: {getattr(consulta, 'session_id', 'N/A')}, "
                f"Status: {getattr(consulta, 'status', 'N/A')}, "
                f"Created at: {getattr(consulta, 'created_at', 'N/A')}"
            )
            
            return consulta
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating Consulta: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating Consulta: {str(e)}")
            raise
    
    def find_by_session(self, session_id: uuid.UUID) -> List[Consulta]:
        """
        Find all consultas by session ID.
        
        Args:
            session_id: The session UUID to search for
            
        Returns:
            List of Consulta instances for the given session
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            consultas = self.session.query(Consulta).filter(
                Consulta.session_id == session_id
            ).order_by(Consulta.created_at.desc()).all()
            
            self.logger.info(f"Found {len(consultas)} consultas for session {session_id}")
            return consultas
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error finding consultas by session {session_id}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error finding consultas by session {session_id}: {str(e)}")
            raise
    
    def find_by_status(self, status: str) -> List[Consulta]:
        """
        Find all consultas by status.
        
        Args:
            status: The status to filter by
            
        Returns:
            List of Consulta instances with the specified status
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            consultas = self.session.query(Consulta).filter(
                Consulta.status == status
            ).order_by(Consulta.created_at.desc()).all()
            
            self.logger.info(f"Found {len(consultas)} consultas with status '{status}'")
            return consultas
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error finding consultas by status '{status}': {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error finding consultas by status '{status}': {str(e)}")
            raise
    
    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Consulta]:
        """
        Find all consultas within a date range.
        
        Args:
            start_date: Start of the date range (inclusive)
            end_date: End of the date range (inclusive)
            
        Returns:
            List of Consulta instances within the date range
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            consultas = self.session.query(Consulta).filter(
                Consulta.created_at >= start_date,
                Consulta.created_at <= end_date
            ).order_by(Consulta.created_at.desc()).all()
            
            self.logger.info(
                f"Found {len(consultas)} consultas between "
                f"{start_date.strftime('%Y-%m-%d %H:%M:%S')} and "
                f"{end_date.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            return consultas
            
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error finding consultas by date range "
                f"({start_date} to {end_date}): {str(e)}"
            )
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error finding consultas by date range "
                f"({start_date} to {end_date}): {str(e)}"
            )
            raise
    
    def find_pending(self) -> List[Consulta]:
        """
        Find all consultas with 'pendente' status.
        
        Returns:
            List of pending Consulta instances
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            consultas = self.session.query(Consulta).filter(
                Consulta.status == 'pendente'
            ).order_by(Consulta.created_at.asc()).all()
            
            self.logger.info(f"Found {len(consultas)} pending consultas")
            return consultas
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error finding pending consultas: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error finding pending consultas: {str(e)}")
            raise
    
    def find_by_session_and_status(self, session_id: uuid.UUID, status: str) -> List[Consulta]:
        """
        Find consultas by both session ID and status.
        
        Args:
            session_id: The session UUID to search for
            status: The status to filter by
            
        Returns:
            List of Consulta instances matching both criteria
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            consultas = self.session.query(Consulta).filter(
                Consulta.session_id == session_id,
                Consulta.status == status
            ).order_by(Consulta.created_at.desc()).all()
            
            self.logger.info(
                f"Found {len(consultas)} consultas for session {session_id} "
                f"with status '{status}'"
            )
            return consultas
            
        except SQLAlchemyError as e:
            self.logger.error(
                f"Error finding consultas by session {session_id} and status '{status}': {str(e)}"
            )
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error finding consultas by session {session_id} "
                f"and status '{status}': {str(e)}"
            )
            raise
    
    def update_status(self, id: int, new_status: str) -> Optional[Consulta]:
        """
        Update the status of a specific consulta.
        
        Args:
            id: The ID of the consulta to update
            new_status: The new status to set
            
        Returns:
            The updated Consulta instance if found, None otherwise
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            consulta = self.session.query(Consulta).filter(Consulta.id == id).first()
            
            if not consulta:
                self.logger.warning(f"Cannot update status for consulta with ID {id}: not found")
                return None
            
            old_status = consulta.status
            consulta.status = new_status
            self.session.commit()
            self.session.refresh(consulta)
            
            self.logger.info(
                f"Updated consulta {id} status from '{old_status}' to '{new_status}'"
            )
            return consulta
            
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating status for consulta {id}: {str(e)}")
            raise
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Unexpected error updating status for consulta {id}: {str(e)}")
            raise
    
    def get_recent_consultas(self, limit: int = 10) -> List[Consulta]:
        """
        Get the most recent consultas.
        
        Args:
            limit: Maximum number of recent consultas to return
            
        Returns:
            List of recent Consulta instances
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            consultas = self.session.query(Consulta).order_by(
                Consulta.created_at.desc()
            ).limit(limit).all()
            
            self.logger.info(f"Retrieved {len(consultas)} recent consultas (limit: {limit})")
            return consultas
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving recent consultas: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving recent consultas: {str(e)}")
            raise 