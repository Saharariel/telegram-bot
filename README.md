# Authentik User Registration Telegram Bot

A secure Telegram bot that automates user registration for Authentik authentication platform with integrated Cloudflare Access policy management.

## Features

- **Secure Bot Access**: Password protection to prevent unauthorized use
- **Comprehensive Validation**:
  - Email format and uniqueness validation
  - Username validation (length, allowed characters)
  - Password strength requirements
  - Duplicate detection for usernames and emails
- **TOTP 2FA Enrollment**: Direct link to TOTP setup flow in Authentik
- **Cloudflare Access Integration**: Automatically adds registered users to Cloudflare Access policies
- **Error Handling**: Graceful handling of duplicate entries and API errors
- **Docker Ready**: Multi-stage hardened Dockerfile for secure deployment

## Prerequisites

- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Authentik instance with API access
- (Optional) Cloudflare Access with API token
- (Optional) Jellyfin media server

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd telegram-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your credentials

4. Run the bot:
```bash
python main.py
```

## Configuration

### Required Environment Variables

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN="your-telegram-bot-token"

# Authentik Configuration
AUTHENTIK_URL="https://authentik.example.com"
AUTHENTIK_API_TOKEN="your-authentik-api-token"

# Bot Access Control
BOT_PASSWORD="your-secure-bot-password"

# Jellyfin Configuration (Optional)
JELLYFIN_URL="https://jellyfin.example.com"
```

### Optional: Cloudflare Access Integration

To automatically add registered users to Cloudflare Access policies:

```bash
# Cloudflare Access Configuration
CF_API_TOKEN="your-cloudflare-api-token"
CF_ACCOUNT_ID="your-cloudflare-account-id"
CF_ACCESS_POLICY_ID="your-access-policy-id"
```

## Usage

### User Registration Flow

1. User starts conversation with bot: `/start`
2. Bot requests access password
3. User provides bot password
4. Bot requests email address
5. User provides email (validated and checked for duplicates)
6. Bot requests username
7. User provides username (validated and checked for duplicates)
8. Bot requests password
9. User provides password (strength validated)
10. Bot creates user account in Authentik
11. (Optional) Bot adds email to Cloudflare Access policy
12. Bot provides TOTP enrollment link
13. User sets up 2FA and types "done"
14. Bot provides Jellyfin access instructions