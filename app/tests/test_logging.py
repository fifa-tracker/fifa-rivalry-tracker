import pytest
import logging
from app.utils.logging import get_logger, setup_logging


def test_get_logger():
    """Test that get_logger returns a properly configured logger"""
    logger = get_logger(__name__)
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == __name__


def test_setup_logging():
    """Test that setup_logging configures logging correctly"""
    # Test with different log levels
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        setup_logging(log_level=level)
        logger = get_logger(__name__)
        assert logger.level == getattr(logging, level)


def test_setup_logging_invalid_level():
    """Test that setup_logging handles invalid log levels gracefully"""
    # This should not raise an exception
    setup_logging(log_level="INVALID_LEVEL")
    logger = get_logger(__name__)
    # Should default to INFO level
    assert logger.level == logging.INFO


def test_logger_output(caplog):
    """Test that loggers output messages correctly"""
    setup_logging(log_level="DEBUG")
    logger = get_logger(__name__)
    
    test_message = "Test log message"
    logger.info(test_message)
    
    assert test_message in caplog.text
    assert "INFO" in caplog.text
    assert __name__ in caplog.text


def test_logger_levels(caplog):
    """Test that different log levels work correctly"""
    setup_logging(log_level="INFO")
    logger = get_logger(__name__)
    
    # Debug message should not appear when level is INFO
    logger.debug("Debug message")
    assert "Debug message" not in caplog.text
    
    # Info message should appear
    logger.info("Info message")
    assert "Info message" in caplog.text
    
    # Warning message should appear
    logger.warning("Warning message")
    assert "Warning message" in caplog.text 