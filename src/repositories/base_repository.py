from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.core.database import Base
import logging

# Type variable for the model
T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    """
    Generic base repository implementing the Repository pattern.
    
    This class provides common CRUD operations for any SQLAlchemy model.
    It uses dependency injection for the database session and includes
    comprehensive error handling and logging.
    """
    
    def __init__(self, model: type[T], session: Session):
        """
        Initialize the repository with a model class and database session.
        
        Args:
            model: The SQLAlchemy model class
            session: The database session instance
        """
        self.model = model
        self.session = session
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new record in the database.
        
        Args:
            data: Dictionary containing the data to create the record
            
        Returns:
            The created model instance
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            instance = self.model(**data)
            self.session.add(instance)
            self.session.commit()
            self.session.refresh(instance)
            
            self.logger.info(f"Created {self.model.__name__} with ID: {getattr(instance, 'id', 'unknown')}")
            return instance
            
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Unexpected error creating {self.model.__name__}: {str(e)}")
            raise
    
    def get(self, id: int) -> Optional[T]:
        """
        Retrieve a record by its ID.
        
        Args:
            id: The ID of the record to retrieve
            
        Returns:
            The model instance if found, None otherwise
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            instance = self.session.query(self.model).filter(self.model.id == id).first()
            
            if instance:
                self.logger.debug(f"Retrieved {self.model.__name__} with ID: {id}")
            else:
                self.logger.debug(f"{self.model.__name__} with ID {id} not found")
                
            return instance
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving {self.model.__name__} with ID {id}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving {self.model.__name__} with ID {id}: {str(e)}")
            raise
    
    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an existing record by its ID.
        
        Args:
            id: The ID of the record to update
            data: Dictionary containing the data to update
            
        Returns:
            The updated model instance if found and updated, None otherwise
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            instance = self.session.query(self.model).filter(self.model.id == id).first()
            
            if not instance:
                self.logger.warning(f"Cannot update {self.model.__name__} with ID {id}: not found")
                return None
            
            # Update only the provided fields
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
                else:
                    self.logger.warning(f"Field '{key}' not found in {self.model.__name__}")
            
            self.session.commit()
            self.session.refresh(instance)
            
            self.logger.info(f"Updated {self.model.__name__} with ID: {id}")
            return instance
            
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating {self.model.__name__} with ID {id}: {str(e)}")
            raise
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Unexpected error updating {self.model.__name__} with ID {id}: {str(e)}")
            raise
    
    def delete(self, id: int) -> bool:
        """
        Delete a record by its ID.
        
        Args:
            id: The ID of the record to delete
            
        Returns:
            True if the record was deleted, False if not found
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            instance = self.session.query(self.model).filter(self.model.id == id).first()
            
            if not instance:
                self.logger.warning(f"Cannot delete {self.model.__name__} with ID {id}: not found")
                return False
            
            self.session.delete(instance)
            self.session.commit()
            
            self.logger.info(f"Deleted {self.model.__name__} with ID: {id}")
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error deleting {self.model.__name__} with ID {id}: {str(e)}")
            raise
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Unexpected error deleting {self.model.__name__} with ID {id}: {str(e)}")
            raise
    
    def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Retrieve a list of records with pagination.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            instances = self.session.query(self.model).offset(skip).limit(limit).all()
            
            self.logger.debug(f"Retrieved {len(instances)} {self.model.__name__} records (skip: {skip}, limit: {limit})")
            return instances
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error listing {self.model.__name__} records: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error listing {self.model.__name__} records: {str(e)}")
            raise
    
    def count(self) -> int:
        """
        Get the total count of records.
        
        Returns:
            Total number of records
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            count = self.session.query(self.model).count()
            self.logger.debug(f"Count of {self.model.__name__} records: {count}")
            return count
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error counting {self.model.__name__} records: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error counting {self.model.__name__} records: {str(e)}")
            raise
    
    def exists(self, id: int) -> bool:
        """
        Check if a record exists by its ID.
        
        Args:
            id: The ID of the record to check
            
        Returns:
            True if the record exists, False otherwise
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            exists = self.session.query(self.model).filter(self.model.id == id).first() is not None
            self.logger.debug(f"{self.model.__name__} with ID {id} exists: {exists}")
            return exists
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error checking existence of {self.model.__name__} with ID {id}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error checking existence of {self.model.__name__} with ID {id}: {str(e)}")
            raise 