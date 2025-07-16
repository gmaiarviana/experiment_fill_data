"""
SQLAlchemy database connection and session management.

This module provides database connection setup, session factory,
and table creation utilities for the Data Structuring Agent.
"""

import logging
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from .config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Create declarative base for models
Base = declarative_base()

# Global engine and session factory
_engine: Optional[object] = None
_SessionLocal: Optional[sessionmaker] = None

# Create default engine instance for easy import
engine = None


def get_engine() -> object:
    """
    Get the database engine instance, creating it if necessary.
    
    Returns:
        Engine: SQLAlchemy engine instance
    """
    global _engine, engine
    if _engine is None:
        settings = get_settings()
        logger.info(f"Creating database engine for: {settings.DATABASE_URL}")
        _engine = create_engine(settings.DATABASE_URL)
        engine = _engine
    return _engine


def create_session_factory() -> sessionmaker:
    """
    Create session factory for database sessions.
    
    Returns:
        sessionmaker: SQLAlchemy session factory
    """
    global _SessionLocal
    
    if _SessionLocal is not None:
        return _SessionLocal
    
    engine = get_engine()
    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    return _SessionLocal


def get_session_factory() -> sessionmaker:
    """
    Get the session factory instance, creating it if necessary.
    
    Returns:
        sessionmaker: SQLAlchemy session factory
    """
    return create_session_factory()


def get_db() -> Session:
    """
    Get a database session instance.
    
    Yields:
        Session: SQLAlchemy database session
        
    Note:
        This function is designed to be used as a dependency in FastAPI.
        The session will be automatically closed when the context exits.
    """
    session_factory = get_session_factory()
    db = session_factory()
    
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables() -> bool:
    """
    Create all database tables defined in models.
    
    Returns:
        bool: True if tables were created successfully, False otherwise
        
    Raises:
        SQLAlchemyError: If table creation fails
    """
    try:
        engine = get_engine()
        
        logger.info("Creating database tables...")
        
        # Import models here to avoid circular imports
        # This will be expanded as models are created
        # from .models import Consulta, ExtractionLog, ChatSession
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database tables created successfully")
        return True
        
    except SQLAlchemyError as e:
        error_msg = f"Failed to create database tables: {str(e)}"
        logger.error(error_msg)
        raise SQLAlchemyError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error creating tables: {str(e)}"
        logger.error(error_msg)
        raise SQLAlchemyError(error_msg) from e


def drop_tables() -> bool:
    """
    Drop all database tables (use with caution).
    
    Returns:
        bool: True if tables were dropped successfully, False otherwise
        
    Raises:
        SQLAlchemyError: If table dropping fails
    """
    try:
        engine = get_engine()
        
        logger.warning("Dropping all database tables...")
        
        Base.metadata.drop_all(bind=engine)
        
        logger.info("Database tables dropped successfully")
        return True
        
    except SQLAlchemyError as e:
        error_msg = f"Failed to drop database tables: {str(e)}"
        logger.error(error_msg)
        raise SQLAlchemyError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error dropping tables: {str(e)}"
        logger.error(error_msg)
        raise SQLAlchemyError(error_msg) from e


def test_connection() -> bool:
    """
    Test database connection and return status.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        engine = get_engine()
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        
        logger.info("Database connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False


def close_connections() -> None:
    """
    Close all database connections and reset global variables.
    
    This is useful for cleanup during application shutdown.
    """
    global _engine, _SessionLocal
    
    if _engine is not None:
        _engine.dispose()
        _engine = None
        logger.info("Database engine disposed")
    
    _SessionLocal = None
    logger.info("Database connections closed") 