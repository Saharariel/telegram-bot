#!/usr/bin/env python3
"""Quick test of Authentik API token."""

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

print("Testing Authentik API Token...")
print(f"URL: {AUTHENTIK_URL}")
print(f"Token (first 10 chars): {AUTHENTIK_API_TOKEN[:10] if AUTHENTIK_API_TOKEN else 'N/A'}")
print()

headers = {
    'Authorization': f'Bearer {AUTHENTIK_API_TOKEN}',
    'Content-Type': 'application/json'
}

try:
    response = requests.get(
        f"{AUTHENTIK_URL}/api/v3/core/users/",
        headers=headers,
        timeout=10
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✅ SUCCESS! Token is valid and working!")
        try:
            data = response.json()
            user_count = data.get('pagination', {}).get('count', len(data.get('results', [])))
            print(f"Found {user_count} users")
        except:
            pass
    elif response.status_code == 403:
        print("❌ FORBIDDEN (403)")
        try:
            error = response.json()
            print(f"Error: {error.get('detail', 'Unknown')}")
        except:
            print(f"Response: {response.text[:200]}")

        print("\nThe token is invalid or expired. You need to:")
        print("1. Go to Authentik: https://auth.saharserver.com/if/admin/#/core/tokens")
        print("2. Delete old token")
        print("3. Create new token with:")
        print("   - Intent: API")
        print("   - User: Superuser account")
        print("   - Expiring: Unchecked (never expires)")
        print("4. Copy new token to .env file")
    elif response.status_code == 401:
        print("❌ UNAUTHORIZED (401)")
        print("The token format is invalid")
    else:
        print(f"❌ Unexpected status: {response.status_code}")
        print(f"Response: {response.text[:200]}")

except Exception as e:
    print(f"❌ Error: {e}")
