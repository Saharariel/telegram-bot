"""Command handlers (/cancel, etc)."""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the registration process."""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Registration cancelled. Use /start to begin again."
    )
    return ConversationHandler.END
