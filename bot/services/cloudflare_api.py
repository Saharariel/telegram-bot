"""Cloudflare API service module."""
import logging
from bot.utils.config import CF_API_TOKEN, CF_ACCOUNT_ID, CF_ACCESS_POLICY_ID

logger = logging.getLogger(__name__)

# Check if Cloudflare is configured
CLOUDFLARE_ENABLED = all([CF_API_TOKEN, CF_ACCOUNT_ID, CF_ACCESS_POLICY_ID])

if CLOUDFLARE_ENABLED:
    try:
        from bot.services.cloudflare_access import add_email_to_access_policy
        logger.info("Cloudflare Access module loaded successfully")
    except ImportError:
        logger.warning("cloudflare_access module not found, Cloudflare integration disabled")
        CLOUDFLARE_ENABLED = False
else:
    logger.warning("Cloudflare Access credentials not configured, Cloudflare integration disabled")


async def add_email_to_access(email: str) -> bool:
    """Add email to Cloudflare Access policy."""
    if not CLOUDFLARE_ENABLED:
        logger.warning("Cloudflare Access is not enabled")
        return False

    try:
        logger.info(f"Adding {email} to Cloudflare Access policy...")
        success = add_email_to_access_policy(email)

        if success:
            logger.info(f"Successfully added {email} to Cloudflare Access policy")
            return True
        else:
            logger.warning(f"Failed to add {email} to Cloudflare Access policy")
            return False

    except Exception as e:
        logger.error(f"Error adding email to Cloudflare Access: {str(e)}", exc_info=True)
        return False
