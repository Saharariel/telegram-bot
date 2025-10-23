import logging
import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Enable logging FIRST
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import Cloudflare Access functions
try:
    from cloudflare_access import add_email_to_access_group, add_email_to_access_policy
    CLOUDFLARE_ENABLED = True
except ImportError:
    logger.warning("cloudflare_access.py not found, Cloudflare integration disabled")
    CLOUDFLARE_ENABLED = False

# Load environment variables from .env file
load_dotenv()

# Conversation states
BOT_PASSWORD, EMAIL, USERNAME, PASSWORD, TOTP_CONFIRM = range(5)

# Configuration - Set these as environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
AUTHENTIK_URL = os.getenv('AUTHENTIK_URL')  # e.g., https://auth.yourdomain.com
AUTHENTIK_API_TOKEN = os.getenv('AUTHENTIK_API_TOKEN')
JELLYFIN_URL = os.getenv('JELLYFIN_URL')  # e.g., https://jellyfin.yourdomain.com
BOT_ACCESS_PASSWORD = os.getenv('BOT_PASSWORD')  # Password to use the bot

# Debug: Print what was loaded (first few chars only for security)
logger.info(f"Loaded TELEGRAM_BOT_TOKEN: {'Yes' if TELEGRAM_BOT_TOKEN else 'No'}")
logger.info(f"Loaded AUTHENTIK_URL: {AUTHENTIK_URL[:30] if AUTHENTIK_URL else 'No'}...")
logger.info(f"Loaded AUTHENTIK_API_TOKEN: {'Yes' if AUTHENTIK_API_TOKEN else 'No'}")
logger.info(f"Loaded JELLYFIN_URL: {JELLYFIN_URL[:30] if JELLYFIN_URL else 'No'}...")
logger.info(f"Loaded BOT_PASSWORD: {'Yes' if BOT_ACCESS_PASSWORD else 'No (bot is public!)'}")

# Authentik API headers
HEADERS = {
    'Authorization': f'Bearer {AUTHENTIK_API_TOKEN}',
    'Content-Type': 'application/json'
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the registration conversation."""
    # If bot password is configured, ask for it first
    if BOT_ACCESS_PASSWORD:
        await update.message.reply_text(
            "Welcome to the Registration Bot!\n\n"
            "🔐 This bot is password-protected.\n\n"
            "Please enter the bot access password to continue.\n\n"
            "Use /cancel to exit."
        )
        return BOT_PASSWORD
    else:
        # No password configured, proceed directly to email
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


async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store email and ask for username."""
    user_email = update.message.text.strip().lower()

    # Email validation
    # Check basic format
    if '@' not in user_email or '.' not in user_email:
        await update.message.reply_text(
            "❌ That doesn't look like a valid email address.\n\n"
            "Please enter a valid email (e.g., user@example.com):"
        )
        return EMAIL

    # Check for spaces
    if ' ' in user_email:
        await update.message.reply_text(
            "❌ Email addresses cannot contain spaces.\n\n"
            "Please enter a valid email:"
        )
        return EMAIL

    # Check for @ position
    at_index = user_email.index('@')
    if at_index == 0 or at_index == len(user_email) - 1:
        await update.message.reply_text(
            "❌ Invalid email format.\n\n"
            "Please enter a valid email (e.g., user@example.com):"
        )
        return EMAIL

    # Check domain has a dot
    domain = user_email.split('@')[1]
    if '.' not in domain or domain.startswith('.') or domain.endswith('.'):
        await update.message.reply_text(
            "❌ Invalid email domain.\n\n"
            "Please enter a valid email (e.g., user@example.com):"
        )
        return EMAIL

    # Check length
    if len(user_email) < 5 or len(user_email) > 254:
        await update.message.reply_text(
            "❌ Email address is too short or too long.\n\n"
            "Please enter a valid email:"
        )
        return EMAIL

    context.user_data['email'] = user_email
    await update.message.reply_text(
        f"✅ Email: {user_email}\n\n"
        "Now, please choose a username (letters, numbers, underscores, and hyphens only):"
    )
    return USERNAME


async def username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store username and ask for password."""
    user_username = update.message.text.strip()

    # Username validation
    # Check length
    if len(user_username) < 3:
        await update.message.reply_text(
            "❌ Username must be at least 3 characters long.\n\n"
            "Please try again:"
        )
        return USERNAME

    if len(user_username) > 150:
        await update.message.reply_text(
            "❌ Username is too long (maximum 150 characters).\n\n"
            "Please try again:"
        )
        return USERNAME

    # Check for spaces
    if ' ' in user_username:
        await update.message.reply_text(
            "❌ Username cannot contain spaces.\n\n"
            "Please try again:"
        )
        return USERNAME

    # Check allowed characters (letters, numbers, underscores, hyphens, periods)
    if not user_username.replace('_', '').replace('-', '').replace('.', '').isalnum():
        await update.message.reply_text(
            "❌ Username can only contain:\n"
            "• Letters (a-z, A-Z)\n"
            "• Numbers (0-9)\n"
            "• Underscores (_)\n"
            "• Hyphens (-)\n"
            "• Periods (.)\n\n"
            "Please try again:"
        )
        return USERNAME

    # Check doesn't start or end with special characters
    if user_username[0] in '.-_' or user_username[-1] in '.-_':
        await update.message.reply_text(
            "❌ Username cannot start or end with special characters.\n\n"
            "Please try again:"
        )
        return USERNAME

    # Check for consecutive special characters
    if '..' in user_username or '__' in user_username or '--' in user_username:
        await update.message.reply_text(
            "❌ Username cannot contain consecutive special characters (e.g., .. or __ or --).\n\n"
            "Please try again:"
        )
        return USERNAME

    context.user_data['username'] = user_username
    await update.message.reply_text(
        f"✅ Username: {user_username}\n\n"
        "Finally, please choose a secure password (at least 8 characters):"
    )
    return PASSWORD


async def password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store password and create user in Authentik."""
    user_password = update.message.text.strip()

    # Password validation
    # Check minimum length
    if len(user_password) < 8:
        await update.message.reply_text(
            "❌ Password must be at least 8 characters long.\n\n"
            "Please try again:"
        )
        return PASSWORD

    # Check maximum length
    if len(user_password) > 128:
        await update.message.reply_text(
            "❌ Password is too long (maximum 128 characters).\n\n"
            "Please try again:"
        )
        return PASSWORD

    # Check for common weak passwords
    common_weak_passwords = [
        'password', '12345678', 'qwerty', 'abc123', 'letmein',
        'welcome', 'monkey', '1234567890', 'password123'
    ]
    if user_password.lower() in common_weak_passwords:
        await update.message.reply_text(
            "❌ This password is too common and easy to guess.\n\n"
            "Please choose a stronger password:"
        )
        return PASSWORD

    # Check password strength (optional but recommended)
    has_upper = any(c.isupper() for c in user_password)
    has_lower = any(c.islower() for c in user_password)
    has_digit = any(c.isdigit() for c in user_password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in user_password)

    strength_score = sum([has_upper, has_lower, has_digit, has_special])

    if strength_score < 2:
        await update.message.reply_text(
            "❌ Password is too weak. Your password should contain:\n"
            "• At least 2 of the following:\n"
            "  - Uppercase letters (A-Z)\n"
            "  - Lowercase letters (a-z)\n"
            "  - Numbers (0-9)\n"
            "  - Special characters (!@#$%^&*)\n\n"
            "Please try again with a stronger password:"
        )
        return PASSWORD

    context.user_data['password'] = user_password

    # Delete the password message for security
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Could not delete password message: {e}")

    await update.message.reply_text(
        "⏳ Creating your account... Please wait."
    )

    # Create user in Authentik
    result = await create_authentik_user(update, context)

    # create_authentik_user now returns a state (TOTP_CONFIRM) or False
    if result == TOTP_CONFIRM:
        return TOTP_CONFIRM
    else:
        # Clear stored data on failure
        context.user_data.clear()
        return ConversationHandler.END


async def check_email_exists(email: str) -> bool:
    """Check if an email is already registered in Authentik."""
    try:
        # Search for users with this email
        response = requests.get(
            f"{AUTHENTIK_URL}/api/v3/core/users/?search={email}",
            headers=HEADERS,
            timeout=10
        )

        if response.status_code == 200:
            users = response.json().get('results', [])

            # Check if any user has this exact email (case-insensitive)
            for user in users:
                if user.get('email', '').lower() == email.lower():
                    logger.info(f"Email {email} already exists for user {user.get('username')}")
                    return True

            return False
        else:
            logger.warning(f"Failed to check email existence: {response.status_code}")
            # If we can't check, allow creation to proceed (fail open)
            return False

    except Exception as e:
        logger.error(f"Error checking email existence: {e}")
        # If we can't check, allow creation to proceed (fail open)
        return False


async def create_authentik_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Create user in Authentik."""
    try:
        email = context.user_data['email']
        username = context.user_data['username']
        password = context.user_data['password']

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
        
        # Step 1: Create user
        user_data = {
            "username": username,
            "email": email,
            "name": username,
            "is_active": True,
            "password": password
        }
        
        logger.info(f"Creating user: {username}")
        logger.info(f"Request URL: {AUTHENTIK_URL}/api/v3/core/users/")
        logger.info(f"Request headers: {dict((k, v[:20] + '...' if len(v) > 20 else v) for k, v in HEADERS.items())}")
        
        response = requests.post(
            f"{AUTHENTIK_URL}/api/v3/core/users/",
            json=user_data,
            headers=HEADERS
        )
        
        # Debug logging
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        logger.info(f"Response text (first 500 chars): {response.text[:500]}")

        if response.status_code not in [200, 201]:
            error_msg = response.text or "Unknown error"

            try:
                error_json = response.json()

                # Check for specific field errors
                if 'username' in error_json:
                    username_errors = error_json['username']

                    # Check for duplicate username
                    if any('unique' in str(err).lower() for err in username_errors):
                        await update.message.reply_text(
                            f"❌ The username '{username}' is already taken.\n\n"
                            "Please try again with a different username.\n"
                            "Use /start to begin again."
                        )
                        logger.error(f"Username already exists: {username}")
                        return False

                    # Check for invalid username format
                    if any('invalid' in str(err).lower() or 'valid' in str(err).lower() for err in username_errors):
                        await update.message.reply_text(
                            f"❌ The username '{username}' is invalid.\n\n"
                            f"Error: {', '.join(str(e) for e in username_errors)}\n\n"
                            "Use /start to try again."
                        )
                        logger.error(f"Invalid username format: {username}")
                        return False

                    # Check for required field
                    if any('required' in str(err).lower() for err in username_errors):
                        await update.message.reply_text(
                            "❌ Username is required.\n\n"
                            "Use /start to begin again."
                        )
                        logger.error("Username field is required")
                        return False

                if 'email' in error_json:
                    email_errors = error_json['email']

                    # Check for duplicate email
                    if any('unique' in str(err).lower() for err in email_errors):
                        await update.message.reply_text(
                            f"❌ The email '{email}' is already registered.\n\n"
                            "Please try again with a different email.\n"
                            "Use /start to begin again."
                        )
                        logger.error(f"Email already exists: {email}")
                        return False

                    # Check for invalid email format
                    if any('invalid' in str(err).lower() or 'valid' in str(err).lower() or 'enter a valid' in str(err).lower() for err in email_errors):
                        await update.message.reply_text(
                            f"❌ The email '{email}' is invalid.\n\n"
                            f"Error: {', '.join(str(e) for e in email_errors)}\n\n"
                            "Use /start to try again."
                        )
                        logger.error(f"Invalid email format: {email}")
                        return False

                    # Check for required field
                    if any('required' in str(err).lower() for err in email_errors):
                        await update.message.reply_text(
                            "❌ Email is required.\n\n"
                            "Use /start to begin again."
                        )
                        logger.error("Email field is required")
                        return False

                if 'password' in error_json:
                    password_errors = error_json['password']

                    # Check for password requirements
                    if any('short' in str(err).lower() or 'minimum' in str(err).lower() for err in password_errors):
                        await update.message.reply_text(
                            "❌ Password doesn't meet the requirements.\n\n"
                            f"Error: {', '.join(str(e) for e in password_errors)}\n\n"
                            "Use /start to try again."
                        )
                        logger.error(f"Password doesn't meet requirements")
                        return False

                    # Check for common passwords
                    if any('common' in str(err).lower() for err in password_errors):
                        await update.message.reply_text(
                            "❌ This password is too common.\n\n"
                            "Please choose a more unique password.\n"
                            "Use /start to try again."
                        )
                        logger.error("Password is too common")
                        return False

                    # Check for numeric-only passwords
                    if any('numeric' in str(err).lower() or 'entirely numeric' in str(err).lower() for err in password_errors):
                        await update.message.reply_text(
                            "❌ Password cannot be entirely numeric.\n\n"
                            "Please include letters or special characters.\n"
                            "Use /start to try again."
                        )
                        logger.error("Password is entirely numeric")
                        return False

                # Check for non_field_errors (general errors)
                if 'non_field_errors' in error_json:
                    non_field_errors = error_json['non_field_errors']
                    error_text = '\n'.join(str(e) for e in non_field_errors)
                    await update.message.reply_text(
                        f"❌ Account creation failed:\n\n"
                        f"{error_text}\n\n"
                        "Use /start to try again."
                    )
                    logger.error(f"Non-field errors: {non_field_errors}")
                    return False

                # Check for general detail message
                if 'detail' in error_json:
                    error_detail = error_json['detail']
                    await update.message.reply_text(
                        f"❌ Failed to create user:\n\n"
                        f"{error_detail}\n\n"
                        "Use /start to try again."
                    )
                    logger.error(f"User creation failed with detail: {error_detail}")
                    return False

                # If we got here, there's an error but we don't recognize the format
                error_detail = str(error_json)
            except:
                error_detail = error_msg

            logger.error(f"User creation failed: {response.status_code} - {error_detail}")
            await update.message.reply_text(
                f"❌ Failed to create user.\n\n"
                f"Error: {error_detail}\n\n"
                "Please try again with /start or contact an administrator."
            )
            return False
        
        # Parse response
        try:
            user_response = response.json()
        except Exception as e:
            logger.error(f"Failed to parse response JSON: {e}")
            logger.error(f"Raw response: {response.text}")
            await update.message.reply_text(
                f"❌ Unexpected response from Authentik. Status: {response.status_code}\n\n"
                "Please check the logs and try again with /start"
            )
            return False
        
        user_pk = user_response.get('pk')
        if not user_pk:
            logger.error(f"No 'pk' in response: {user_response}")
            await update.message.reply_text(
                "❌ User creation returned unexpected data. Please contact an administrator."
            )
            return False
            
        logger.info(f"User created successfully: {user_pk}")

        await update.message.reply_text("✅ User account created!")

        # Add email to Cloudflare Access policy (if configured)
        if CLOUDFLARE_ENABLED:
            logger.info(f"Adding {email} to Cloudflare Access policy...")
            cf_success = add_email_to_access_policy(email)
            if cf_success:
                logger.info(f"Successfully added {email} to Cloudflare Access policy")
                await update.message.reply_text(
                    "✅ Email added to access policy!\n\n"
                    "You now have access to protected services."
                )
            else:
                logger.warning(f"Failed to add {email} to Cloudflare Access policy (non-critical)")
                # Don't fail the registration if Cloudflare update fails

        # Store username and password for later
        context.user_data['username'] = username
        context.user_data['password'] = password

        # Send TOTP enrollment instructions
        await send_totp_instructions(update, context)

        # Return the TOTP_CONFIRM state instead of ending
        return TOTP_CONFIRM
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        await update.message.reply_text(
            f"❌ An error occurred: {str(e)}\n\n"
            "Please try again with /start or contact an administrator."
        )
        return False


async def send_totp_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send TOTP setup instructions and wait for confirmation."""
    username = context.user_data.get('username')

    totp_instructions = f"""
🔐 **Set Up Two-Factor Authentication**

Before you can access Jellyfin, you need to set up 2FA:

**Step 1: Install an Authenticator App**
Download this app on your phone:
• Google Authenticator (Android/iOS)

**Step 2: Enroll Your Device**
Click this link to set up TOTP:
{AUTHENTIK_URL}/if/flow/default-authenticator-totp-setup/

You'll be asked to:
1. Log in with your credentials
2. Scan a QR code with your authenticator app
3. Enter a code to verify it works

**Your Login Credentials:**
• Username: `{username}`
• Password: The password you just created
"""

    await update.message.reply_text(totp_instructions, parse_mode='Markdown')

    # Ask user to confirm when done
    await update.message.reply_text(
        "📱 Once you've completed the 2FA setup, please type 'done' to continue and get your Jellyfin access instructions."
    )


async def send_jellyfin_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send instructions for accessing Jellyfin."""
    username = context.user_data.get('username')

    jellyfin_instructions = f"""
🎬 **Welcome to Jellyfin!**

Your 2FA is now set up! You can access the media server:

**Server URL:** {JELLYFIN_URL}

**Your Credentials:**
• Username: `{username}`
• Password: The password you created earlier

**Login Steps:**
1. Open {JELLYFIN_URL} in your browser
2. Click "Sign In"
3. Enter your username and password
4. Enter the 6-digit code from your authenticator app

**Apps Available:**
• Web browser (any device)
• Android: Jellyfin app from Play Store
• iOS: Jellyfin app from App Store
• Android TV / Fire TV / Roku / etc.

**Need Help?**
Contact the administrator if you have any issues.

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
            "If you need help, contact an administrator.\n"
            "To cancel, use /cancel"
        )
        return TOTP_CONFIRM


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the registration process."""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Registration cancelled. Use /start to begin again."
    )
    return ConversationHandler.END


def main():
    """Start the bot."""
    # Validate configuration
    if not all([TELEGRAM_BOT_TOKEN, AUTHENTIK_URL, AUTHENTIK_API_TOKEN, JELLYFIN_URL]):
        logger.error("Missing required environment variables!")
        logger.error("Please set: TELEGRAM_BOT_TOKEN, AUTHENTIK_URL, AUTHENTIK_API_TOKEN, JELLYFIN_URL")
        return
    
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
    
    # Start the bot
    logger.info("Bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()