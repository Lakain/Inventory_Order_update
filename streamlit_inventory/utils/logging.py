"""
Logging configuration and utilities for the Streamlit application.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

def setup_logging(log_level=logging.INFO):
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (default: INFO)
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create log filename with timestamp
    log_filename = f"inventory_app_{datetime.now().strftime('%Y%m%d')}.log"
    log_path = log_dir / log_filename
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    # Create application logger
    logger = logging.getLogger("inventory_app")
    logger.info("Logging initialized")
    
    return logger

def get_logger(name):
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"inventory_app.{name}")

class StreamlitLogHandler(logging.Handler):
    """Custom log handler to display logs in Streamlit interface."""
    
    def __init__(self, container=None):
        super().__init__()
        self.container = container
        self.logs = []
    
    def emit(self, record):
        """Emit a log record to the Streamlit container."""
        log_entry = self.format(record)
        self.logs.append(log_entry)
        
        if self.container:
            # Display in Streamlit container
            if record.levelno >= logging.ERROR:
                self.container.error(log_entry)
            elif record.levelno >= logging.WARNING:
                self.container.warning(log_entry)
            else:
                self.container.info(log_entry)
    
    def get_logs(self):
        """Get all collected logs."""
        return self.logs
    
    def clear_logs(self):
        """Clear collected logs."""
        self.logs.clear()