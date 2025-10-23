#!/usr/bin/env python3
"""Test TOTP endpoints in Authentik API."""

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
print("TOTP ENDPOINT INVESTIGATION")
print("=" * 70)

headers = {
    'Authorization': f'Bearer {AUTHENTIK_API_TOKEN}',
    'Content-Type': 'application/json'
}

# Check what TOTP-related endpoints exist
print("\n1. Checking available TOTP endpoints...")
print("-" * 70)

endpoints_to_test = [
    "/api/v3/authenticators/totp/",
    "/api/v3/stages/authenticator/totp/",
    "/api/v3/authenticators/all/",
    "/api/v3/core/user_consent/",
]

for endpoint in endpoints_to_test:
    print(f"\nTesting: {endpoint}")
    try:
        # Try OPTIONS to see what methods are allowed
        response = requests.options(
            f"{AUTHENTIK_URL}{endpoint}",
            headers=headers,
            timeout=10
        )

        allowed_methods = response.headers.get('Allow', 'N/A')
        print(f"  Allowed methods: {allowed_methods}")

        # Try GET to see if we can list
        response = requests.get(
            f"{AUTHENTIK_URL}{endpoint}",
            headers=headers,
            timeout=10
        )

        print(f"  GET Status: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and 'results' in data:
                    print(f"  ✓ Found {len(data['results'])} items")
                elif isinstance(data, list):
                    print(f"  ✓ Found {len(data)} items")
                else:
                    print(f"  ✓ Response: {str(data)[:100]}")
            except:
                pass

    except Exception as e:
        print(f"  Error: {e}")

# Check the API schema/documentation
print("\n" + "=" * 70)
print("2. Checking API schema for authenticator endpoints...")
print("-" * 70)

try:
    response = requests.get(
        f"{AUTHENTIK_URL}/api/v3/schema/",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        print("✓ API schema available")
        # Look for TOTP-related paths
        schema = response.json()

        if 'paths' in schema:
            totp_paths = [path for path in schema['paths'].keys() if 'totp' in path.lower() or 'authenticator' in path.lower()]

            if totp_paths:
                print("\nFound TOTP/Authenticator related paths:")
                for path in totp_paths[:10]:  # Show first 10
                    print(f"  - {path}")
            else:
                print("No TOTP paths found in schema")
    else:
        print(f"Schema not available (status {response.status_code})")

except Exception as e:
    print(f"Error fetching schema: {e}")

# Try to understand how to enroll TOTP for a user
print("\n" + "=" * 70)
print("3. Looking for user-specific TOTP enrollment...")
print("-" * 70)

# First, get a test user
try:
    response = requests.get(
        f"{AUTHENTIK_URL}/api/v3/core/users/?page_size=1",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        users = response.json().get('results', [])
        if users:
            test_user_pk = users[0]['pk']
            test_username = users[0]['username']
            print(f"\nUsing test user: {test_username} (pk: {test_user_pk})")

            # Try different TOTP enrollment approaches
            print("\nTrying different TOTP enrollment patterns:")

            # Pattern 1: Admin-enrolled TOTP device
            print("\n  a) Admin enrollment via /api/v3/authenticators/admin/totp/")
            try:
                response = requests.post(
                    f"{AUTHENTIK_URL}/api/v3/authenticators/admin/totp/",
                    json={"user": test_user_pk},
                    headers=headers,
                    timeout=10
                )
                print(f"     Status: {response.status_code}")
                if response.status_code in [200, 201]:
                    print(f"     ✅ SUCCESS! This endpoint works!")
                    print(f"     Response: {response.json()}")
                else:
                    print(f"     Response: {response.text[:200]}")
            except Exception as e:
                print(f"     Error: {e}")

            # Pattern 2: Using stages endpoint
            print("\n  b) Via stages endpoint")
            try:
                response = requests.get(
                    f"{AUTHENTIK_URL}/api/v3/stages/authenticator/totp/",
                    headers=headers,
                    timeout=10
                )
                print(f"     GET Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"     Available TOTP stages: {response.json()}")
            except Exception as e:
                print(f"     Error: {e}")

    else:
        print("Could not get users for testing")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("RECOMMENDATIONS:")
print("=" * 70)

print("""
Based on the tests above, we'll identify the correct endpoint for TOTP enrollment.

Common patterns in Authentik:

1. Admin-enrolled devices (automatic setup by admin):
   POST /api/v3/authenticators/admin/totp/

2. User self-enrollment (requires user interaction):
   POST /api/v3/authenticators/totp/

3. Using a flow/stage (more complex):
   Requires setting up an enrollment flow

For a Telegram bot, you likely want ADMIN enrollment so users
don't have to go through the web interface.
""")

print("=" * 70)
