#!/usr/bin/env python3
"""Test user creation in Authentik API."""

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

print("=" * 70)
print("TEST USER CREATION")
print("=" * 70)

headers = {
    'Authorization': f'Bearer {AUTHENTIK_API_TOKEN}',
    'Content-Type': 'application/json'
}

# Test data - using a test username that's unlikely to exist
test_user = {
    "username": "testuser_" + str(os.getpid()),  # Unique username based on process ID
    "email": f"test{os.getpid()}@example.com",
    "name": "Test User",
    "is_active": True,
    "password": "TestPassword123!"
}

print(f"\nAttempting to create test user: {test_user['username']}")
print("-" * 70)

try:
    response = requests.post(
        f"{AUTHENTIK_URL}/api/v3/core/users/",
        json=test_user,
        headers=headers,
        timeout=10
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code in [200, 201]:
        print("\n✅ SUCCESS! User created successfully!")
        user_data = response.json()
        print(f"\nUser details:")
        print(f"  - Username: {user_data.get('username')}")
        print(f"  - Email: {user_data.get('email')}")
        print(f"  - User PK: {user_data.get('pk')}")
        print(f"  - Is Active: {user_data.get('is_active')}")

        print(f"\n🧹 Cleaning up - deleting test user...")
        # Clean up by deleting the test user
        delete_response = requests.delete(
            f"{AUTHENTIK_URL}/api/v3/core/users/{user_data.get('pk')}/",
            headers=headers,
            timeout=10
        )

        if delete_response.status_code == 204:
            print("✅ Test user deleted successfully")
        else:
            print(f"⚠️  Could not delete test user (status {delete_response.status_code})")
            print(f"   You may need to manually delete user: {test_user['username']}")

        print("\n" + "=" * 70)
        print("🎉 YOUR BOT IS READY TO USE!")
        print("=" * 70)
        print("\nYou can now start your Telegram bot with:")
        print("  python3 main.py")
        print("\nThe bot will be able to:")
        print("  ✓ Create users in Authentik")
        print("  ✓ Set up TOTP authentication")
        print("  ✓ Send Jellyfin access instructions")

    elif response.status_code == 400:
        print("\n⚠️  Bad Request (400)")
        try:
            error = response.json()
            print(f"Error details: {error}")
        except:
            print(f"Response: {response.text}")
        print("\nThis might mean:")
        print("  - Required fields are missing")
        print("  - Password doesn't meet requirements")
        print("  - Username format is invalid")

    elif response.status_code == 403:
        print("\n❌ FORBIDDEN (403)")
        print("The token doesn't have permission to create users")
        print("\nCheck that:")
        print("  - The user who owns the token is a superuser")
        print("  - The token intent is 'API'")

    else:
        print(f"\n⚠️  Unexpected status: {response.status_code}")
        print(f"Response: {response.text[:300]}")

except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 70)
