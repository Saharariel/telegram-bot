"""Validation functions for user input."""


def validate_email(email: str) -> tuple[bool, str]:
    """Validate email format."""
    email = email.strip().lower()

    # Check basic format
    if '@' not in email or '.' not in email:
        return False, "That doesn't look like a valid email address."

    # Check for spaces
    if ' ' in email:
        return False, "Email addresses cannot contain spaces."

    # Check for @ position
    at_index = email.index('@')
    if at_index == 0 or at_index == len(email) - 1:
        return False, "Invalid email format."

    # Check domain has a dot
    domain = email.split('@')[1]
    if '.' not in domain or domain.startswith('.') or domain.endswith('.'):
        return False, "Invalid email domain."

    # Check length
    if len(email) < 5 or len(email) > 254:
        return False, "Email address is too short or too long."

    return True, email


def validate_username(username: str) -> tuple[bool, str]:
    """Validate username format."""
    username = username.strip()

    # Check length
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."

    if len(username) > 150:
        return False, "Username is too long (maximum 150 characters)."

    # Check for spaces
    if ' ' in username:
        return False, "Username cannot contain spaces."

    # Check allowed characters (letters, numbers, underscores, hyphens, periods)
    if not username.replace('_', '').replace('-', '').replace('.', '').isalnum():
        return False, "Username can only contain letters, numbers, underscores (_), hyphens (-), and periods (.)."

    # Check doesn't start or end with special characters
    if username[0] in '.-_' or username[-1] in '.-_':
        return False, "Username cannot start or end with special characters."

    # Check for consecutive special characters
    if '..' in username or '__' in username or '--' in username:
        return False, "Username cannot contain consecutive special characters."

    return True, username


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    password = password.strip()

    # Check minimum length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    # Check maximum length
    if len(password) > 128:
        return False, "Password is too long (maximum 128 characters)."

    # Check for common weak passwords
    common_weak_passwords = [
        'password', '12345678', 'qwerty', 'abc123', 'letmein',
        'welcome', 'monkey', '1234567890', 'password123'
    ]
    if password.lower() in common_weak_passwords:
        return False, "This password is too common and easy to guess."

    # Check password strength
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)

    strength_score = sum([has_upper, has_lower, has_digit, has_special])

    if strength_score < 2:
        return False, "Password is too weak. Should contain at least 2 of: uppercase, lowercase, numbers, special characters."

    return True, password
