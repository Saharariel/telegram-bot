"""TOTP handlers (setup and confirmation)."""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bot.utils.config import AUTHENTIK_URL, JELLYFIN_URL
from .auth import TOTP_CONFIRM

logger = logging.getLogger(__name__)


async def send_totp_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send TOTP setup instructions and wait for confirmation."""
    username = context.user_data.get('username')

    totp_instructions = f"""
🔐 **Set Up Two-Factor Authentication**

Before you can access Jellyfin, you need to set up 2FA (TOTP):

**Step 1: Install an Authenticator App**
Download this app on your phone:
• Google Authenticator (Android/iOS)

**Step 2: Log In to Authentik**
First, you need to log in to your account:
🔗 {AUTHENTIK_URL}

Use these credentials:
• Username: `{username}`
• Password: The password you just created

**Step 3: Enroll Your Authenticator**
After logging in, click this link to set up TOTP:
🔗 {AUTHENTIK_URL}/if/flow/default-authenticator-totp-setup/

You'll be asked to:
1. Scan a QR code with your authenticator app
2. Enter the 6-digit code to verify it works
3. The setup is complete!

**Summary:**
1️⃣ Log in: {AUTHENTIK_URL}
2️⃣ Set up TOTP: {AUTHENTIK_URL}/if/flow/default-authenticator-totp-setup/
3️⃣ Type 'done' below when finished

**Important:** Keep your authenticator app safe - you'll need it every time you log in!
"""

    await update.message.reply_text(totp_instructions, parse_mode='Markdown')

    # Ask user to confirm when done
    await update.message.reply_text(
        "📱 Once you've completed the 2FA setup, please type 'done' to continue and get your Jellyfin access instructions."
    )


async def send_jellyfin_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send instructions for accessing Jellyfin."""
    username = context.user_data.get('username')
    email = context.user_data.get('email')

    jellyfin_instructions = f"""
🎬 **Welcome to the Media Server!**

Your 2FA is now set up! You can access the media server:

**Server URL:** {JELLYFIN_URL}

**Step 1: Cloudflare Access Authentication**
Before accessing Jellyfin, you must pass through Cloudflare Access:

1. Open {JELLYFIN_URL} in your browser
2. You will be redirected to Cloudflare Access login
3. Enter your email: `{email}`
4. A one-time PIN will be sent to your email
5. Check your email and enter the one-time PIN
6. You will be granted access to Jellyfin

**Step 2: Jellyfin Login**
After passing Cloudflare Access:

1. You will be redirected to Jellyfin
2. Click "Sign In"
3. Enter your username: `{username}`
4. For the password field, enter: `<your-password>;<6-digit-totp-code>`
   (Example: `MyPassword123;456789`)
   - Replace `<your-password>` with your actual password
   - Replace `<6-digit-totp-code>` with the current code from your authenticator app

**Apps Available:**
• Web browser (any device)
• Android: Jellyfin app from Play Store
• iOS: Jellyfin app from App Store
• Android TV / Fire TV / Roku / etc.

Enjoy your media! 🍿
"""

    await update.message.reply_text(jellyfin_instructions, parse_mode='Markdown')


async def totp_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle TOTP confirmation from user."""
    user_response = update.message.text.strip().lower()

    if user_response == 'done':
        await update.message.reply_text("✅ Great! Let me send you the Jellyfin access instructions...")

        # Send Jellyfin instructions
        await send_jellyfin_instructions(update, context)

        # Clear stored data
        context.user_data.clear()

        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "⏳ Please type 'done' when you've finished setting up 2FA.\n\n"
            "To cancel, use /cancel"
        )
        return TOTP_CONFIRM
