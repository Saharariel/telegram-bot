"""Configuration module for loading environment variables."""
import os
import logging
from dotenv import load_dotenv

# Enable logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BOT_ACCESS_PASSWORD = os.getenv('BOT_PASSWORD')

# Authentik Configuration
AUTHENTIK_URL = os.getenv('AUTHENTIK_URL')
AUTHENTIK_API_TOKEN = os.getenv('AUTHENTIK_API_TOKEN')
JELLYFIN_URL = os.getenv('JELLYFIN_URL')

# Cloudflare Configuration (Optional)
CF_API_TOKEN = os.getenv('CF_API_TOKEN')
CF_ACCOUNT_ID = os.getenv('CF_ACCOUNT_ID')
CF_ACCESS_POLICY_ID = os.getenv('CF_ACCESS_POLICY_ID')

# Authentik API headers
AUTHENTIK_HEADERS = {
    'Authorization': f'Bearer {AUTHENTIK_API_TOKEN}',
    'Content-Type': 'application/json'
}

# Debug: Print what was loaded (first few chars only for security)
logger.info(f"Loaded TELEGRAM_BOT_TOKEN: {'Yes' if TELEGRAM_BOT_TOKEN else 'No'}")
logger.info(f"Loaded AUTHENTIK_URL: {AUTHENTIK_URL[:30] if AUTHENTIK_URL else 'No'}...")
logger.info(f"Loaded AUTHENTIK_API_TOKEN: {'Yes' if AUTHENTIK_API_TOKEN else 'No'}")
logger.info(f"Loaded JELLYFIN_URL: {JELLYFIN_URL[:30] if JELLYFIN_URL else 'No'}...")
logger.info(f"Loaded BOT_PASSWORD: {'Yes' if BOT_ACCESS_PASSWORD else 'No (bot is public!)'}")


def validate_config() -> bool:
    """Validate that all required configuration is set."""
    if not all([TELEGRAM_BOT_TOKEN, AUTHENTIK_URL, AUTHENTIK_API_TOKEN, JELLYFIN_URL]):
        logger.error("Missing required environment variables!")
        logger.error("Please set: TELEGRAM_BOT_TOKEN, AUTHENTIK_URL, AUTHENTIK_API_TOKEN, JELLYFIN_URL")
        return False
    return True
