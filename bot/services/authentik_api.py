"""Authentik API service module."""

import logging
import requests
from bot.utils.config import AUTHENTIK_URL, AUTHENTIK_HEADERS

logger = logging.getLogger(__name__)


async def check_email_exists(email: str) -> bool:
    """Check if an email is already registered in Authentik."""
    try:
        response = requests.get(
            f"{AUTHENTIK_URL}/api/v3/core/users/?search={email}",
            headers=AUTHENTIK_HEADERS,
            timeout=10,
        )

        if response.status_code == 200:
            users = response.json().get("results", [])
            for user in users:
                if user.get("email", "").lower() == email.lower():
                    logger.info(
                        f"Email {email} already exists for user {user.get('username')}"
                    )
                    return True
            return False
        else:
            logger.warning(f"Failed to check email existence: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Error checking email existence: {e}")
        return False


async def create_user(username: str, email: str, password: str) -> dict | None:
    """Create user in Authentik. Returns user data with pk or None on failure."""
    try:
        # Step 1: Create user (without password)
        user_data = {
            "username": username,
            "email": email,
            "name": username,
            "is_active": True,
            # Don't include password here - it won't work
        }
        logger.info(f"Creating user: {username}")
        response = requests.post(
            f"{AUTHENTIK_URL}/api/v3/core/users/",
            json=user_data,
            headers=AUTHENTIK_HEADERS,
        )
        logger.info(f"Response status: {response.status_code}")

        if response.status_code not in [200, 201]:
            error_msg = response.text or "Unknown error"
            logger.error(f"User creation failed: {response.status_code} - {error_msg}")
            return None

        user_response = response.json()
        user_pk = user_response.get("pk")

        if not user_pk:
            logger.error(f"No 'pk' in response: {user_response}")
            return None

        logger.info(f"User created successfully: {user_pk}")

        # Step 2: Set the password
        password_response = requests.post(
            f"{AUTHENTIK_URL}/api/v3/core/users/{user_pk}/set_password/",
            json={"password": password},
            headers=AUTHENTIK_HEADERS,
        )

        if password_response.status_code not in [200, 204]:
            logger.error(
                f"Password setting failed: {password_response.status_code} - {password_response.text}"
            )
            # User exists but password not set - you may want to handle this

        logger.info(f"Password set for user: {user_pk}")
        return user_response

    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        return None


async def add_user_to_group(user_pk: int, group_name: str = "Jellyfin Users") -> bool:
    """Add user to a group in Authentik."""
    try:
        # Step 1: Get the group by name
        logger.info(f"Looking up group '{group_name}'...")
        groups_response = requests.get(
            f"{AUTHENTIK_URL}/api/v3/core/groups/?search={group_name}",
            headers=AUTHENTIK_HEADERS,
            timeout=10,
        )

        if groups_response.status_code != 200:
            logger.warning(f"Failed to fetch groups: {groups_response.status_code}")
            return False

        groups = groups_response.json().get("results", [])

        # Find group with exact name match
        group_pk = None
        group_data = None
        for group in groups:
            if group.get("name", "").lower() == group_name.lower():
                group_pk = group.get("pk")
                group_data = group
                break

        if not group_pk:
            logger.warning(f"Group '{group_name}' not found in Authentik")
            return False

        logger.info(f"Found group '{group_name}' with pk={group_pk}")

        # Step 2: Get current users in the group
        current_users = group_data.get("users", [])
        logger.info(f"Current users in group: {current_users}")

        # Check if user is already in group
        if user_pk in current_users:
            logger.info(f"User {user_pk} is already in group '{group_name}'")
            return True

        # Step 3: Add user to group by PATCH request with updated user list
        updated_users = current_users + [user_pk]
        logger.info(f"Adding user {user_pk} to group '{group_name}'...")

        patch_response = requests.patch(
            f"{AUTHENTIK_URL}/api/v3/core/groups/{group_pk}/",
            json={"users": updated_users},
            headers=AUTHENTIK_HEADERS,
            timeout=10,
        )

        if patch_response.status_code in [200, 204]:
            logger.info(f"Successfully added user {user_pk} to group '{group_name}'")
            return True
        else:
            logger.warning(
                f"Failed to add user to group: {patch_response.status_code} - {patch_response.text}"
            )
            return False

    except Exception as e:
        logger.error(f"Error adding user to group: {str(e)}", exc_info=True)
        return False
