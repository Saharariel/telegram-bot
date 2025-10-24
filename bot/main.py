"""Main bot application."""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from bot.utils.config import TELEGRAM_BOT_TOKEN, validate_config
from bot.handlers.auth import start, bot_password, BOT_PASSWORD, EMAIL, USERNAME, PASSWORD
from bot.handlers.registration import email, username, password
from bot.handlers.totp import totp_confirm
from bot.handlers.commands import cancel
from bot.handlers.auth import TOTP_CONFIRM

logger = logging.getLogger(__name__)


def create_app() -> Application:
    """Create and configure the bot application."""
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BOT_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_password)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password)],
            TOTP_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, totp_confirm)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    return application


def run():
    """Run the bot."""
    # Validate configuration
    if not validate_config():
        return

    # Create application
    application = create_app()

    # Start the bot with optimized polling
    logger.info("Bot started...")
    # Polling parameters:
    # - poll_interval: seconds between polling requests (default 0, meaning continuous)
    # - timeout: how long to wait for updates (long polling, reduces requests)
    # - allowed_updates: only listen for message and command updates (not all update types)
    application.run_polling(
        poll_interval=1.0,  # Wait 1 second between polls
        timeout=30,  # Long polling timeout (server holds connection for 30 seconds)
        allowed_updates=[Update.MESSAGE, Update.CALLBACK_QUERY]
    )


if __name__ == '__main__':
    run()
