"""Logging configuration for SolarNode"""
import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

def setup_logging():
    """Configure logging to file and console."""
    log_file = LOG_DIR / 'solarnode.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set specific levels
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('flask').setLevel(logging.INFO)

    return logging.getLogger(__name__)

# Create a default logger
logger = setup_logging()
