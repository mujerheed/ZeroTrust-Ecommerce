"""
Structured JSON logging.
"""

import logging
import os
from pythonjsonlogger import jsonlogger

# Get logger
logger = logging.getLogger("trustguard")

# Only configure if not already configured (prevents duplicate handlers)
if not logger.handlers:
    # Set log level from environment or default to INFO
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level))
    
    # Create handler
    handler = logging.StreamHandler()
    
    # Create JSON formatter with more useful fields
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(funcName)s %(lineno)d %(message)s"
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to root logger (avoids duplicate logs)
    logger.propagate = False
