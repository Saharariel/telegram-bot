#!/usr/bin/env python3
"""Test duplicate email error handling."""

import os
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

headers = {
    'Authorization': f'Bearer {AUTHENTIK_API_TOKEN}',
    'Content-Type': 'application/json'
}

print("=" * 70)
print("TEST DUPLICATE EMAIL ERROR HANDLING")
print("=" * 70)

# Get an existing user with an email
print("\n1. Finding a user with an email...")
try:
    response = requests.get(
        f"{AUTHENTIK_URL}/api/v3/core/users/",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        users = response.json().get('results', [])

        # Find a user with an email
        existing_email = None
        existing_username = None

        for user in users:
            if user.get('email'):
                existing_email = user['email']
                existing_username = user['username']
                break

        if existing_email:
            print(f"✓ Found user with email: {existing_email}")
            print(f"  (Username: {existing_username})")

            # Try to create a new user with the same email
            print(f"\n2. Attempting to create new user with duplicate email...")
            print("-" * 70)

            new_user_data = {
                "username": f"newuser_{os.getpid()}",  # Unique username
                "email": existing_email,  # Duplicate email
                "name": "Test User",
                "is_active": True,
                "password": "TestPassword123!"
            }

            print(f"Creating user:")
            print(f"  Username: {new_user_data['username']}")
            print(f"  Email: {new_user_data['email']} (duplicate)")

            response = requests.post(
                f"{AUTHENTIK_URL}/api/v3/core/users/",
                json=new_user_data,
                headers=headers,
                timeout=10
            )

            print(f"\nResponse:")
            print(f"  Status Code: {response.status_code}")

            if response.status_code == 400:
                error_json = response.json()
                print(f"  Error JSON: {error_json}")

                if 'email' in error_json:
                    email_errors = error_json['email']
                    print(f"\n✅ Duplicate email detected correctly!")
                    print(f"   Server error: {email_errors}")

                    # Check if our validation logic would catch it
                    if any('unique' in str(err).lower() for err in email_errors):
                        print(f"\n   ✅ Bot will show:")
                        print(f"   ❌ The email '{existing_email}' is already registered.")
                        print(f"      Please try again with a different email.")
                        print(f"      Use /start to begin again.")
                    else:
                        print(f"\n   ⚠️  'unique' not found in error message")
                else:
                    print(f"\n   ⚠️  'email' field not in error response")
                    print(f"   Full error: {error_json}")

            elif response.status_code == 201:
                print(f"\n⚠️  UNEXPECTED: User was created (email might not be unique constraint)")
                user_data = response.json()
                print(f"   User PK: {user_data.get('pk')}")

                # Clean up - delete the test user
                print(f"\n   Cleaning up test user...")
                delete_response = requests.delete(
                    f"{AUTHENTIK_URL}/api/v3/core/users/{user_data.get('pk')}/",
                    headers=headers,
                    timeout=10
                )
                if delete_response.status_code == 204:
                    print(f"   ✓ Test user deleted")

            else:
                print(f"\n   Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text[:200]}")

        else:
            print("⚠️  No users found with email addresses")
            print("   Creating a test user with email first...")

    else:
        print(f"❌ Failed to get users: {response.status_code}")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print("""
Testing duplicate email validation:

If Authentik enforces unique emails:
  ✅ Server returns 400 with {"email": ["This field must be unique."]}
  ✅ Bot catches this and shows friendly error message
  ✅ User knows to use a different email

If Authentik doesn't enforce unique emails:
  ⚠️  Multiple users can have the same email
  ⚠️  This is a configuration choice in Authentik
  ⚠️  Bot will still work, just won't catch duplicate emails

To test the full flow:
  1. Start your bot: python3 main.py
  2. Register with an existing email address
  3. You should see: "The email 'X' is already registered."
""")

print("=" * 70)
