#!/usr/bin/env python3
"""Test if we can get a TOTP enrollment link for users."""

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
print("TOTP ENROLLMENT LINK INVESTIGATION")
print("=" * 70)

print("""
In Authentik, there are a few ways users can enroll TOTP:

1. Direct link to the TOTP enrollment flow
2. User settings page where they can add devices
3. Using an enrollment token/link

Let's check what's available...
""")

# Check if there's a TOTP enrollment flow
print("\n1. Checking for TOTP enrollment flows...")
print("-" * 70)

try:
    response = requests.get(
        f"{AUTHENTIK_URL}/api/v3/flows/instances/?designation=stage_configuration",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        flows = response.json().get('results', [])
        print(f"Found {len(flows)} stage configuration flows")

        totp_flows = [f for f in flows if 'totp' in f.get('slug', '').lower()]

        if totp_flows:
            print("\nTOTP Enrollment Flows:")
            for flow in totp_flows:
                slug = flow.get('slug')
                title = flow.get('title')
                print(f"\n  Flow: {title}")
                print(f"  Slug: {slug}")
                print(f"  Direct link: {AUTHENTIK_URL}/if/flow/{slug}/")
                print(f"  ^^ Users can visit this link to enroll TOTP!")
        else:
            print("\nNo TOTP-specific flows found, but checking all flows:")
            for flow in flows:
                print(f"  - {flow.get('title')} ({flow.get('slug')})")

except Exception as e:
    print(f"Error: {e}")

# Check user interface endpoints
print("\n2. User self-service TOTP enrollment...")
print("-" * 70)

print(f"""
Users can typically enroll TOTP devices through their profile:

User Settings URL:
{AUTHENTIK_URL}/if/user/#/settings

Users can:
1. Log in to Authentik
2. Go to their user settings
3. Navigate to "MFA Devices" or "Authenticators"
4. Click "Enroll" to add a new TOTP device
5. Scan the QR code with their authenticator app

This is the RECOMMENDED approach because:
- It's secure (secret never leaves Authentik)
- QR code is generated on-demand
- User can verify it works before saving
""")

# Check if we can use enrollment invitation links
print("\n3. Checking for enrollment/invitation system...")
print("-" * 70)

try:
    response = requests.get(
        f"{AUTHENTIK_URL}/api/v3/stages/invitation/invitations/",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        print("✓ Invitation system is available")
        print("  You could create invitation links that require TOTP setup")
    elif response.status_code == 404:
        print("  Invitation system not found")
    else:
        print(f"  Status: {response.status_code}")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
print("RECOMMENDATION")
print("=" * 70)

print(f"""
The BEST approach is to send users a direct link to enroll TOTP:

After creating the user account, send them:

1. Login credentials (username/password)
2. Direct link to TOTP enrollment flow (if one exists)
   OR
   Link to user settings page where they can add authenticators

Typical TOTP enrollment URLs in Authentik:

→ {AUTHENTIK_URL}/if/flow/default-authenticator-totp-setup/
  (This is the standard TOTP enrollment flow)

→ {AUTHENTIK_URL}/if/user/#/settings
  (User settings page where they can add devices)

Let me check if the default TOTP flow exists...
""")

# Try to access the default TOTP flow
print("\n4. Testing default TOTP enrollment flow...")
print("-" * 70)

try:
    # Try without auth (public flow)
    response = requests.get(
        f"{AUTHENTIK_URL}/if/flow/default-authenticator-totp-setup/",
        timeout=10,
        allow_redirects=False
    )

    print(f"Status: {response.status_code}")

    if response.status_code in [200, 302]:
        print(f"\n✅ TOTP enrollment flow exists!")
        print(f"\nSend users this link: {AUTHENTIK_URL}/if/flow/default-authenticator-totp-setup/")
        print("\nThey'll need to:")
        print("  1. Log in (if not already logged in)")
        print("  2. Follow the TOTP setup wizard")
        print("  3. Scan QR code with their authenticator app")
        print("  4. Verify with a code")

    elif response.status_code == 404:
        print("❌ Default TOTP flow not found")
        print(f"\nUse the generic user settings link instead:")
        print(f"   {AUTHENTIK_URL}/if/user/#/settings")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 70)
