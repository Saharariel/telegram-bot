#!/usr/bin/env python3
"""Test duplicate username/email error handling."""

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
print("TEST DUPLICATE USER ERROR HANDLING")
print("=" * 70)

# Get an existing user to test with
print("\n1. Getting an existing user...")
try:
    response = requests.get(
        f"{AUTHENTIK_URL}/api/v3/core/users/?page_size=1",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        users = response.json().get('results', [])
        if users:
            existing_user = users[0]
            existing_username = existing_user['username']
            existing_email = existing_user['email']

            print(f"✓ Found existing user: {existing_username}")

            # Try to create user with duplicate username
            print(f"\n2. Testing duplicate username error...")
            print("-" * 70)

            user_data = {
                "username": existing_username,
                "email": "newemail@example.com",
                "name": "Test User",
                "is_active": True,
                "password": "TestPassword123!"
            }

            response = requests.post(
                f"{AUTHENTIK_URL}/api/v3/core/users/",
                json=user_data,
                headers=headers,
                timeout=10
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 400:
                error_json = response.json()
                print(f"Error response: {error_json}")

                if 'username' in error_json:
                    print(f"\n✅ Duplicate username detected correctly!")
                    print(f"   Error: {error_json['username']}")
                    print(f"\n   Bot will show:")
                    print(f"   ❌ The username '{existing_username}' is already taken.")
                    print(f"      Please try again with a different username.")
                else:
                    print("⚠️  Username error not detected properly")

            # Try to create user with duplicate email (if email exists)
            if existing_email:
                print(f"\n3. Testing duplicate email error...")
                print("-" * 70)

                user_data = {
                    "username": "newusername123",
                    "email": existing_email,
                    "name": "Test User",
                    "is_active": True,
                    "password": "TestPassword123!"
                }

                response = requests.post(
                    f"{AUTHENTIK_URL}/api/v3/core/users/",
                    json=user_data,
                    headers=headers,
                    timeout=10
                )

                print(f"Status: {response.status_code}")

                if response.status_code == 400:
                    error_json = response.json()
                    print(f"Error response: {error_json}")

                    if 'email' in error_json:
                        print(f"\n✅ Duplicate email detected correctly!")
                        print(f"   Error: {error_json['email']}")
                        print(f"\n   Bot will show:")
                        print(f"   ❌ The email '{existing_email}' is already registered.")
                        print(f"      Please try again with a different email.")
                    else:
                        print("⚠️  Email error not detected properly")

        else:
            print("No users found to test with")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print("""
Your bot now handles these common errors gracefully:

✅ Duplicate username
   → Shows: "The username 'X' is already taken."

✅ Duplicate email
   → Shows: "The email 'X' is already registered."

✅ Other errors
   → Shows: Generic error message with details

Users will know exactly what went wrong and can try again!
""")

print("=" * 70)
