"""Authentication handlers (/start, bot password)."""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bot.utils.config import BOT_ACCESS_PASSWORD

logger = logging.getLogger(__name__)

# Conversation states
BOT_PASSWORD, EMAIL, USERNAME, PASSWORD, TOTP_CONFIRM = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the registration conversation."""
    if BOT_ACCESS_PASSWORD:
        await update.message.reply_text(
            "Welcome to the Registration Bot!\n\n"
            "🔐 This bot is password-protected.\n\n"
            "Please enter the bot access password to continue.\n\n"
            "Use /cancel to exit."
        )
        return BOT_PASSWORD
    else:
        await update.message.reply_text(
            "Welcome to the Media Server Registration Bot!\n\n"
            "I'll help you create an account and set up secure access to our Jellyfin media server.\n\n"
            "Let's get started!\n Please send me your email address.\n\n"
            "Use /cancel at any time to stop the registration."
        )
        return EMAIL


async def bot_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Verify bot access password."""
    user_password = update.message.text.strip()

    # Delete the password message for security
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Could not delete bot password message: {e}")

    # Check if password matches
    if user_password == BOT_ACCESS_PASSWORD:
        logger.info(f"User {update.effective_user.username or update.effective_user.id} authenticated successfully")
        await update.message.reply_text(
            "✅ Access granted!\n\n"
            "Please send me your email address."
        )
        return EMAIL
    else:
        logger.warning(f"Failed bot password attempt from {update.effective_user.username or update.effective_user.id}")
        await update.message.reply_text(
            "❌ Incorrect password.\n\n"
            "Access denied. Please contact the administrator if you need access.\n\n"
            "Use /start to try again."
        )
        return ConversationHandler.END
