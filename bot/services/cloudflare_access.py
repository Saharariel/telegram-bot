"""
Cloudflare Access API integration for adding users to policies.
"""

import os
import requests
import logging

logger = logging.getLogger(__name__)

# Cloudflare API configuration
CF_API_TOKEN = os.getenv('CF_API_TOKEN')
CF_ACCOUNT_ID = os.getenv('CF_ACCOUNT_ID')
CF_ACCESS_POLICY_ID = os.getenv('CF_ACCESS_POLICY_ID')  # The policy to add users to


def add_email_to_access_policy(email: str) -> bool:
    """
    Add an email to a Cloudflare Access policy.

    Args:
        email: User's email address to add to the policy

    Returns:
        bool: True if successful, False otherwise
    """
    if not all([CF_API_TOKEN, CF_ACCOUNT_ID, CF_ACCESS_POLICY_ID]):
        logger.warning("Cloudflare Access credentials not configured, skipping policy update")
        return False

    try:
        # First, get the current policy to see its structure
        headers = {
            'Authorization': f'Bearer {CF_API_TOKEN}',
            'Content-Type': 'application/json'
        }

        # Get the current policy
        get_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/access/policies/{CF_ACCESS_POLICY_ID}"

        logger.info(f"Fetching Cloudflare Access policy {CF_ACCESS_POLICY_ID}")
        response = requests.get(get_url, headers=headers, timeout=10)

        if response.status_code != 200:
            logger.error(f"Failed to fetch Cloudflare policy: {response.status_code} - {response.text}")
            return False

        policy = response.json()['result']

        # Check if the policy has an 'include' section
        if 'include' not in policy:
            policy['include'] = []

        # Check if email already exists in policy
        email_exists = False
        for rule in policy['include']:
            if 'email' in rule and isinstance(rule['email'], dict):
                if rule['email'].get('email', '').lower() == email.lower():
                    email_exists = True
                    logger.info(f"Email {email} already exists in policy")
                    break

        # If email doesn't exist, add it as a new rule
        if not email_exists:
            policy['include'].append({
                'email': {'email': email.lower()}
            })
            logger.info(f"Added new email rule for {email}")

            # Update the policy
            logger.info(f"Updating Cloudflare Access policy")
            response = requests.put(
                get_url,
                headers=headers,
                json=policy,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Successfully added {email} to Cloudflare Access policy")
                return True
            else:
                logger.error(f"Failed to update Cloudflare policy: {response.status_code} - {response.text}")
                return False
        else:
            # Email already exists, return True
            return True

    except Exception as e:
        logger.error(f"Error adding email to Cloudflare Access: {e}", exc_info=True)
        return False


def add_email_to_access_group(email: str) -> bool:
    """
    Alternative: Add email to a Cloudflare Access Group instead of directly to policy.
    This is cleaner and more maintainable.

    Args:
        email: User's email address to add to the group

    Returns:
        bool: True if successful, False otherwise
    """
    CF_ACCESS_GROUP_ID = os.getenv('CF_ACCESS_GROUP_ID')

    if not all([CF_API_TOKEN, CF_ACCOUNT_ID, CF_ACCESS_GROUP_ID]):
        logger.warning("Cloudflare Access Group credentials not configured")
        return False

    try:
        headers = {
            'Authorization': f'Bearer {CF_API_TOKEN}',
            'Content-Type': 'application/json'
        }

        # Get the current group
        get_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/access/groups/{CF_ACCESS_GROUP_ID}"

        logger.info(f"Fetching Cloudflare Access group {CF_ACCESS_GROUP_ID}")
        response = requests.get(get_url, headers=headers, timeout=10)

        if response.status_code != 200:
            logger.error(f"Failed to fetch Cloudflare group: {response.status_code} - {response.text}")
            return False

        group = response.json()['result']

        # Add email to the group's include list
        if 'include' not in group:
            group['include'] = []

        # Check if email already exists
        email_exists = False
        for rule in group['include']:
            if 'email' in rule:
                if isinstance(rule['email'], dict) and rule['email'].get('email') == email.lower():
                    email_exists = True
                    logger.info(f"Email {email} already in group")
                    break

        if not email_exists:
            group['include'].append({
                'email': {'email': email.lower()}
            })

            # Update the group
            logger.info(f"Updating Cloudflare Access group")
            response = requests.put(
                get_url,
                headers=headers,
                json=group,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Successfully added {email} to Cloudflare Access group")
                return True
            else:
                logger.error(f"Failed to update Cloudflare group: {response.status_code} - {response.text}")
                return False

        return True

    except Exception as e:
        logger.error(f"Error adding email to Cloudflare Access group: {e}", exc_info=True)
        return False
