import os
import sys
from loguru import logger


def setup_logging():
    """
    Configura o sistema de logging com Loguru de forma simplificada.
    
    Configurações:
    - Formato JSON estruturado via serialize=True
    - Log level via variável de ambiente LOG_LEVEL (default: INFO)
    - Output para stdout
    """
    
    # Remove handlers padrão do loguru
    logger.remove()
    
    # Configura log level via variável de ambiente
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Adiciona handler para stdout com formato JSON simples
    logger.add(
        sys.stdout,
        level=log_level,
        serialize=True,  # Serializa automaticamente para JSON
        format="{time:YYYY-MM-DDTHH:mm:ss}Z | {level} | {name}:{function}:{line} | {message}"
    )
    
    logger.info(f"Logging configurado com nível: {log_level}")
    
    return logger 