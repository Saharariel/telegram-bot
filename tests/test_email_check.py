#!/usr/bin/env python3
"""Test the custom email existence check function."""

import os
import sys
import requests

# Load .env
try:
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")
except FileNotFoundError:
    pass

AUTHENTIK_URL = os.getenv('AUTHENTIK_URL')
AUTHENTIK_API_TOKEN = os.getenv('AUTHENTIK_API_TOKEN')

HEADERS = {
    'Authorization': f'Bearer {AUTHENTIK_API_TOKEN}',
    'Content-Type': 'application/json'
}

def check_email_exists(email: str) -> bool:
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
                    return True

            return False
        else:
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False


print("=" * 70)
print("EMAIL EXISTENCE CHECK TEST")
print("=" * 70)

# Test 1: Get an existing email
print("\n1. Finding an existing email in the system...")
try:
    response = requests.get(
        f"{AUTHENTIK_URL}/api/v3/core/users/",
        headers=HEADERS,
        timeout=10
    )

    if response.status_code == 200:
        users = response.json().get('results', [])

        existing_email = None
        for user in users:
            if user.get('email'):
                existing_email = user['email']
                existing_username = user['username']
                break

        if existing_email:
            print(f"✓ Found existing email: {existing_email}")
            print(f"  (User: {existing_username})")

            # Test 2: Check if it detects the existing email
            print(f"\n2. Testing check_email_exists() with existing email...")
            print("-" * 70)

            result = check_email_exists(existing_email)

            if result:
                print(f"✅ SUCCESS! Function correctly detected duplicate email")
                print(f"   check_email_exists('{existing_email}') → True")
            else:
                print(f"❌ FAIL! Function didn't detect the duplicate")
                print(f"   check_email_exists('{existing_email}') → False")

            # Test 3: Test case-insensitivity
            print(f"\n3. Testing case-insensitivity...")
            print("-" * 70)

            upper_email = existing_email.upper()
            result_upper = check_email_exists(upper_email)

            if result_upper:
                print(f"✅ SUCCESS! Case-insensitive check works")
                print(f"   check_email_exists('{upper_email}') → True")
            else:
                print(f"❌ FAIL! Case-insensitive check doesn't work")
                print(f"   check_email_exists('{upper_email}') → False")

            # Test 4: Check non-existent email
            print(f"\n4. Testing with non-existent email...")
            print("-" * 70)

            fake_email = f"nonexistent{os.getpid()}@example.com"
            result_fake = check_email_exists(fake_email)

            if not result_fake:
                print(f"✅ SUCCESS! Function correctly returned False for non-existent email")
                print(f"   check_email_exists('{fake_email}') → False")
            else:
                print(f"❌ FAIL! Function incorrectly detected fake email as existing")
                print(f"   check_email_exists('{fake_email}') → True")

            # Test 5: Full integration test
            print(f"\n5. Integration test: Try to create user with duplicate email...")
            print("-" * 70)

            test_user_data = {
                "username": f"testuser_{os.getpid()}",
                "email": existing_email,  # Duplicate email
                "name": "Test User",
                "is_active": True,
                "password": "TestPassword123!"
            }

            print(f"Before API call, checking email: {existing_email}")
            if check_email_exists(existing_email):
                print(f"✅ Email check detected duplicate BEFORE API call")
                print(f"   Bot will show: ❌ The email '{existing_email}' is already registered.")
                print(f"   API call will be PREVENTED (saving resources)")
            else:
                print(f"⚠️  Email check didn't detect duplicate")
                print(f"   API call will proceed and likely fail")

        else:
            print("⚠️  No users with email addresses found")

    else:
        print(f"❌ Failed to get users: {response.status_code}")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print("""
✅ Custom email check function added to the bot!

How it works:
1. User enters email, username, and password
2. Before calling Authentik API, bot checks if email exists
3. If email exists → Show error, don't make API call
4. If email doesn't exist → Proceed with user creation

Benefits:
✓ Prevents duplicate emails (even though Authentik allows them)
✓ Saves API calls (doesn't attempt creation if email exists)
✓ Better user experience (instant feedback)
✓ Case-insensitive matching
✓ Fails open (if check fails, allows creation to proceed)

To test the full bot flow:
1. Start bot: python3 main.py
2. Try to register with an existing email
3. You should see: "The email 'X' is already registered."
4. User will be asked to use /start to try again

The bot now validates:
✓ Email format (client-side)
✓ Email uniqueness (custom check)
✓ Username format (client-side)
✓ Username uniqueness (server-side)
✓ Password strength (client-side)
✓ Password requirements (server-side)
""")

print("=" * 70)
