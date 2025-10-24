#!/usr/bin/env python3
"""
Entry point for running the Telegram Registration Bot.

Usage:
    python run.py

Or with bash:
    ./run.py
"""
import logging
import sys

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

try:
    from bot.main import run
    from bot.utils.config import validate_config

    if __name__ == '__main__':
        if validate_config():
            run()
        else:
            logger.error("Configuration validation failed!")
            sys.exit(1)

except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running this from the project root directory")
    sys.exit(1)
except Exception as e:
    logger.error(f"Fatal error: {e}", exc_info=True)
    sys.exit(1)
