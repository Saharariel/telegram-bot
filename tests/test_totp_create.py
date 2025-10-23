#!/usr/bin/env python3
"""Test TOTP device creation with correct format."""

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
print("TEST TOTP DEVICE CREATION")
print("=" * 70)

headers = {
    'Authorization': f'Bearer {AUTHENTIK_API_TOKEN}',
    'Content-Type': 'application/json'
}

# Get the latest user (the one we just created)
print("\n1. Getting latest user...")
try:
    response = requests.get(
        f"{AUTHENTIK_URL}/api/v3/core/users/?ordering=-date_joined&page_size=1",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        users = response.json().get('results', [])
        if users:
            user = users[0]
            user_pk = user['pk']
            username = user['username']
            print(f"✓ Found user: {username} (pk: {user_pk})")

            # Try to create TOTP device with correct payload
            print(f"\n2. Creating TOTP device for user {username}...")
            print("-" * 70)

            totp_data = {
                "user": user_pk,
                "name": f"{username}_totp_device"
            }

            print(f"Payload: {totp_data}")

            response = requests.post(
                f"{AUTHENTIK_URL}/api/v3/authenticators/admin/totp/",
                json=totp_data,
                headers=headers,
                timeout=10
            )

            print(f"Status: {response.status_code}")

            if response.status_code in [200, 201]:
                print("✅ SUCCESS! TOTP device created")
                totp_result = response.json()
                print(f"\nTOTP Device details:")
                for key, value in totp_result.items():
                    if key == 'config_url':
                        print(f"  - {key}: {value[:50]}... (truncated)")
                    else:
                        print(f"  - {key}: {value}")

                # Check if we have QR code or config URL
                if 'config_url' in totp_result:
                    print(f"\n📱 QR Code URL (for authenticator apps):")
                    print(f"   {totp_result['config_url']}")
                    print("\n   Users should scan this with Google Authenticator, Authy, etc.")

                print("\n🎉 TOTP enrollment working correctly!")

            elif response.status_code == 400:
                print("❌ Bad Request (400)")
                try:
                    error = response.json()
                    print(f"Error: {error}")
                except:
                    print(f"Response: {response.text}")

            elif response.status_code == 405:
                print("❌ Method Not Allowed (405)")
                print("The endpoint doesn't support POST")
                print(f"Response: {response.text}")

            else:
                print(f"⚠️  Status {response.status_code}")
                print(f"Response: {response.text[:300]}")

        else:
            print("❌ No users found")
    else:
        print(f"❌ Could not get users (status {response.status_code})")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
