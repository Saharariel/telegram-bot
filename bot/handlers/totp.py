"""TOTP handlers (setup and confirmation)."""
import logging
import io
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bot.utils.config import AUTHENTIK_URL, JELLYFIN_URL
from bot.services.authentik_api import enroll_totp
from .auth import TOTP_CONFIRM

logger = logging.getLogger(__name__)


async def send_totp_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send TOTP setup instructions with QR code and wait for confirmation."""
    username = context.user_data.get('username')
    password = context.user_data.get('password')

    # Send initial message
    await update.message.reply_text(
        "🔐 **Setting up Two-Factor Authentication (2FA)**\n\n"
        "Please wait while I generate your TOTP enrollment...",
        parse_mode='Markdown'
    )

    # Enroll TOTP and get QR code
    logger.info(f"Enrolling TOTP for user {username}...")
    totp_data = await enroll_totp(username, password)

    if not totp_data or not totp_data.get('qr_code'):
        # Fallback to manual setup if QR generation fails
        logger.warning("QR code generation failed, falling back to manual setup")
        await update.message.reply_text(
            "⚠️ Automated setup failed. Please set up TOTP manually:\n\n"
            f"1. Log in to {AUTHENTIK_URL}\n"
            f"2. Go to {AUTHENTIK_URL}/if/flow/default-authenticator-totp-setup/\n"
            f"3. Follow the instructions to scan the QR code\n"
            f"4. Type 'done' when finished",
            parse_mode='Markdown'
        )
        return

    # Send QR code
    config_url = totp_data.get('config_url', '')
    qr_code_bytes = totp_data.get('qr_code')

    totp_instructions = f"""
🔐 **Two-Factor Authentication Setup**

**Step 1: Install an Authenticator App**
Download one of these apps on your phone:
• Google Authenticator (Android/iOS)
• Microsoft Authenticator (Android/iOS)
• Authy (Android/iOS)

**Step 2: Scan the QR Code**
I'm sending you a QR code below. Open your authenticator app and scan it!

**Step 3: Verify Setup**
After scanning, you'll need to verify the setup by entering a code from your app.

📱 **Please log in to Authentik to complete the verification:**
🔗 {AUTHENTIK_URL}

Username: `{username}`
Password: The password you created

Then type 'done' below when you've completed the verification.

**Important:** Keep your authenticator app safe - you'll need it for every login!
"""

    await update.message.reply_text(totp_instructions, parse_mode='Markdown')

    # Send QR code as photo
    await update.message.reply_photo(
        photo=io.BytesIO(qr_code_bytes),
        caption="📱 Scan this QR code with your authenticator app"
    )

    # Send manual entry option as fallback
    # Extract secret from config_url for manual entry
    manual_entry_text = f"""
**Alternative: Manual Entry**
If you can't scan the QR code, you can manually enter these details in your authenticator app:

Account: `{username}`
Key: Available in the URL above (or scan the QR code)
Type: Time-based

After setup, please type 'done' to continue.
"""

    await update.message.reply_text(manual_entry_text, parse_mode='Markdown')


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
