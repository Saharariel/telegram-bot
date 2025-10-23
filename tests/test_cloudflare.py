#!/usr/bin/env python3
"""
Test script for Cloudflare Access integration.

This script tests:
1. Cloudflare API credentials are valid
2. Account ID is correct
3. Access Group exists and is accessible
4. Can add an email to the group
5. Can verify email was added

Usage:
    python test_cloudflare.py
"""

import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

CF_API_TOKEN = os.getenv('CF_API_TOKEN')
CF_ACCOUNT_ID = os.getenv('CF_ACCOUNT_ID')
CF_ACCESS_POLICY_ID = os.getenv('CF_ACCESS_POLICY_ID')

def test_credentials():
    """Test if Cloudflare API credentials are valid."""
    print("=" * 60)
    print("TEST 1: Validating Cloudflare API Credentials")
    print("=" * 60)

    if not all([CF_API_TOKEN, CF_ACCOUNT_ID, CF_ACCESS_POLICY_ID]):
        print("❌ FAILED: Missing environment variables")
        print(f"   CF_API_TOKEN: {'✓' if CF_API_TOKEN else '✗ Missing'}")
        print(f"   CF_ACCOUNT_ID: {'✓' if CF_ACCOUNT_ID else '✗ Missing'}")
        print(f"   CF_ACCESS_POLICY_ID: {'✓' if CF_ACCESS_POLICY_ID else '✗ Missing'}")
        return False

    # Check if values are still placeholders
    if "your-" in CF_API_TOKEN or "your-" in CF_ACCOUNT_ID or "your-" in CF_ACCESS_POLICY_ID:
        print("❌ FAILED: Environment variables contain placeholder values")
        print("   Please update .env file with actual Cloudflare credentials")
        return False

    print("✅ PASSED: All environment variables are set")
    print(f"   Account ID: {CF_ACCOUNT_ID}")
    print(f"   Policy ID: {CF_ACCESS_POLICY_ID}")
    print(f"   Token: {CF_API_TOKEN[:20]}...{CF_API_TOKEN[-10:]}")
    return True

def test_api_connection():
    """Test if we can connect to Cloudflare API."""
    print("\n" + "=" * 60)
    print("TEST 2: Testing Cloudflare API Connection")
    print("=" * 60)

    try:
        # Test with verify endpoint
        response = requests.get(
            "https://api.cloudflare.com/client/v4/user/tokens/verify",
            headers={
                "Authorization": f"Bearer {CF_API_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ PASSED: API token is valid")
                print(f"   Token Status: {data.get('result', {}).get('status', 'unknown')}")
                return True
            else:
                print("❌ FAILED: API returned success=false")
                print(f"   Errors: {data.get('errors', [])}")
                return False
        else:
            print("❌ FAILED: Invalid status code")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {e}")
        return False

def test_access_policy():
    """Test if we can fetch the Access Policy."""
    print("\n" + "=" * 60)
    print("TEST 3: Fetching Cloudflare Access Policy")
    print("=" * 60)

    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/access/policies/{CF_ACCESS_POLICY_ID}"
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {CF_API_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"URL: {url}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                policy = data.get('result', {})
                print("✅ PASSED: Successfully fetched Access Policy")
                print(f"   Policy Name: {policy.get('name', 'N/A')}")
                print(f"   Policy ID: {policy.get('id', 'N/A')}")

                # Show current includes
                includes = policy.get('include', [])
                print(f"   Current Include Rules: {len(includes)}")

                # Count emails already in policy
                email_count = 0
                for rule in includes:
                    if rule.get('email'):
                        email_count += 1
                        email_value = rule['email'].get('email', 'N/A')
                        print(f"      - {email_value}")

                if email_count == 0:
                    print("      (No emails in policy yet)")

                return True
            else:
                print("❌ FAILED: API returned success=false")
                print(f"   Errors: {data.get('errors', [])}")
                return False
        else:
            print("❌ FAILED: Invalid status code")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {e}")
        return False

def test_add_email():
    """Test adding an email to the Access Policy."""
    print("\n" + "=" * 60)
    print("TEST 4: Adding Test Email to Access Policy")
    print("=" * 60)

    test_email = "test-cloudflare-integration@example.com"
    print(f"Test Email: {test_email}")

    try:
        from cloudflare_access import add_email_to_access_policy
        success = add_email_to_access_policy(test_email)

        if success:
            print("✅ PASSED: Successfully added email to Access Policy")
            print("   (Check Cloudflare dashboard to verify)")
            return True
        else:
            print("❌ FAILED: Function returned False")
            print("   Check logs above for details")
            return False

    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {e}")
        return False

def test_verify_email_added():
    """Verify the test email was actually added."""
    print("\n" + "=" * 60)
    print("TEST 5: Verifying Email Was Added")
    print("=" * 60)

    test_email = "test-cloudflare-integration@example.com"

    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/access/policies/{CF_ACCESS_POLICY_ID}"
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {CF_API_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                policy = data.get('result', {})
                includes = policy.get('include', [])

                # Check if our test email is in the policy
                email_found = False
                for rule in includes:
                    if rule.get('email', {}).get('email') == test_email:
                        email_found = True
                        break

                if email_found:
                    print(f"✅ PASSED: Email '{test_email}' found in Access Policy")
                    return True
                else:
                    print(f"❌ FAILED: Email '{test_email}' NOT found in Access Policy")
                    print("   Current emails in policy:")
                    for rule in includes:
                        if rule.get('email'):
                            print(f"      - {rule['email'].get('email', 'N/A')}")
                    return False
            else:
                print("❌ FAILED: API returned success=false")
                return False
        else:
            print("❌ FAILED: Could not fetch policy")
            return False

    except Exception as e:
        print(f"❌ FAILED: Exception occurred: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CLOUDFLARE ACCESS INTEGRATION TEST SUITE")
    print("=" * 60 + "\n")

    results = []

    # Test 1: Credentials
    results.append(("Credentials Check", test_credentials()))

    if not results[0][1]:
        print("\n" + "=" * 60)
        print("❌ STOPPING: Cannot proceed without valid credentials")
        print("=" * 60)
        print("\nPlease update your .env file with:")
        print("1. CF_API_TOKEN - Get from https://dash.cloudflare.com/profile/api-tokens")
        print("   Required scopes: Access: Applications and Policies:Edit")
        print("2. CF_ACCOUNT_ID - Find in Cloudflare dashboard URL")
        print("3. CF_ACCESS_POLICY_ID - Create a policy in Cloudflare Access first")
        return

    # Test 2: API Connection
    results.append(("API Connection", test_api_connection()))

    if not results[1][1]:
        print("\n❌ STOPPING: Cannot proceed without valid API connection")
        return

    # Test 3: Access Policy
    results.append(("Access Policy Fetch", test_access_policy()))

    if not results[2][1]:
        print("\n❌ STOPPING: Cannot proceed without valid Access Policy")
        return

    # Test 4: Add Email
    results.append(("Add Email", test_add_email()))

    # Test 5: Verify Email
    if results[3][1]:
        results.append(("Verify Email", test_verify_email_added()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! Cloudflare Access integration is working correctly.")
        print("   You can now use the Telegram bot to automatically add users to Cloudflare Access.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")

if __name__ == "__main__":
    main()
