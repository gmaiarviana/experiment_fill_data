from src.core.logging.logger_factory import get_logger

if __name__ == "__main__":
    logger = get_logger("test_logger")
    logger.info("Teste de log estruturado") 