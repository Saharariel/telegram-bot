"""Registration handlers (email, username, password)."""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bot.utils.validators import validate_email, validate_username, validate_password
from bot.services.user_service import create_and_setup_user
from .auth import EMAIL, USERNAME, PASSWORD, TOTP_CONFIRM

logger = logging.getLogger(__name__)


async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store email and ask for username."""
    is_valid, result = validate_email(update.message.text.strip().lower())

    if not is_valid:
        await update.message.reply_text(
            f"❌ {result}\n\n"
            "Please enter a valid email (e.g., user@example.com):"
        )
        return EMAIL

    context.user_data['email'] = result
    await update.message.reply_text(
        f"✅ Email: {result}\n\n"
        "Now, please choose a username (letters, numbers, underscores, and hyphens only):"
    )
    return USERNAME


async def username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store username and ask for password."""
    is_valid, result = validate_username(update.message.text.strip())

    if not is_valid:
        await update.message.reply_text(
            f"❌ {result}\n\n"
            "Please try again:"
        )
        return USERNAME

    context.user_data['username'] = result
    await update.message.reply_text(
        f"✅ Username: {result}\n\n"
        "Finally, please choose a secure password (at least 8 characters):"
    )
    return PASSWORD


async def password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store password and create user in Authentik."""
    is_valid, result = validate_password(update.message.text.strip())

    if not is_valid:
        await update.message.reply_text(
            f"❌ {result}\n\n"
            "Please try again:"
        )
        return PASSWORD

    context.user_data['password'] = result

    # Delete the password message for security
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Could not delete password message: {e}")

    # Create and setup user
    email = context.user_data['email']
    username = context.user_data['username']
    password_value = context.user_data['password']

    success = await create_and_setup_user(update, context, email, username, password_value)

    if success:
        # Send TOTP enrollment instructions
        from .totp import send_totp_instructions
        await send_totp_instructions(update, context)
        return TOTP_CONFIRM
    else:
        # Clear stored data on failure
        context.user_data.clear()
        return ConversationHandler.END
