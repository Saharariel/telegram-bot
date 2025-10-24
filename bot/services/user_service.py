"""User service module containing business logic for user operations."""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.authentik_api import create_user, add_user_to_group, check_email_exists
from bot.services.cloudflare_api import add_email_to_access

logger = logging.getLogger(__name__)


async def create_and_setup_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    email: str,
    username: str,
    password: str
) -> bool:
    """
    Create user in Authentik and set up all integrations.
    Returns True if successful, False otherwise.
    """
    try:
        # Check if email already exists
        logger.info(f"Checking if email {email} already exists...")
        if await check_email_exists(email):
            await update.message.reply_text(
                f"❌ The email '{email}' is already registered.\n\n"
                "Please try again with a different email.\n"
                "Use /start to begin again."
            )
            logger.error(f"Email already exists: {email}")
            return False

        # Create user in Authentik
        await update.message.reply_text(
            "⏳ Creating your account... Please wait."
        )

        user_response = await create_user(username, email, password)

        if not user_response:
            await update.message.reply_text(
                f"❌ Failed to create user.\n\n"
                "Please try again with /start or contact an administrator."
            )
            return False

        user_pk = user_response.get('pk')
        await update.message.reply_text("✅ User account created!")

        # Add user to Jellyfin Users group
        logger.info(f"Adding user {username} to Jellyfin Users group...")
        group_success = await add_user_to_group(user_pk, "Jellyfin Users")
        if group_success:
            logger.info(f"Successfully added {username} to Jellyfin Users group")
            await update.message.reply_text("✅ Added to Jellyfin Users group!")
        else:
            logger.warning(f"Failed to add {username} to Jellyfin Users group (non-critical)")
            await update.message.reply_text(
                "⚠️ Note: Could not automatically add you to Jellyfin Users group.\n"
                "Please contact the administrator to be added manually."
            )

        # Add email to Cloudflare Access policy
        cf_success = await add_email_to_access(email)
        if cf_success:
            await update.message.reply_text(
                "✅ Email added to access policy!\n\n"
                "You now have access to protected services."
            )

        # Store user data for next steps
        context.user_data['username'] = username
        context.user_data['password'] = password
        context.user_data['email'] = email

        return True

    except Exception as e:
        logger.error(f"Error in create_and_setup_user: {str(e)}", exc_info=True)
        await update.message.reply_text(
            f"❌ An error occurred: {str(e)}\n\n"
            "Please try again with /start or contact an administrator."
        )
        return False
