"""Authentik API service module."""

import logging
import authentik_client
from authentik_client.rest import ApiException
from authentik_client.models import UserRequest, UserPasswordSetRequest, UserAccountRequest
from bot.utils.config import AUTHENTIK_URL, AUTHENTIK_API_TOKEN

logger = logging.getLogger(__name__)


def _get_configuration() -> authentik_client.Configuration:
    """Create and return Authentik API configuration."""
    configuration = authentik_client.Configuration(
        host=f"{AUTHENTIK_URL}/api/v3",
        access_token=AUTHENTIK_API_TOKEN
    )
    return configuration


async def check_email_exists(email: str) -> bool:
    """Check if an email is already registered in Authentik."""
    try:
        configuration = _get_configuration()

        with authentik_client.ApiClient(configuration) as api_client:
            api = authentik_client.CoreApi(api_client)

            # Search for users with the email
            users_response = api.core_users_list(search=email)

            # Check if any user has an exact email match
            for user in users_response.results:
                if user.email and user.email.lower() == email.lower():
                    logger.info(
                        f"Email {email} already exists for user {user.username}"
                    )
                    return True

            return False

    except ApiException as e:
        logger.error(f"API exception checking email existence: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking email existence: {e}")
        return False


async def create_user(username: str, email: str, password: str) -> dict | None:
    """Create user in Authentik. Returns user data with pk or None on failure."""
    try:
        configuration = _get_configuration()

        with authentik_client.ApiClient(configuration) as api_client:
            api = authentik_client.CoreApi(api_client)

            # Step 1: Create user (without password)
            user_request = UserRequest(
                username=username,
                email=email,
                name=username,
                is_active=True
            )

            logger.info(f"Creating user: {username}")
            user = api.core_users_create(user_request)

            user_pk = user.pk
            logger.info(f"User created successfully: {user_pk}")

            # Step 2: Set the password
            password_request = UserPasswordSetRequest(password=password)
            api.core_users_set_password_create(user_pk, password_request)

            logger.info(f"Password set for user: {user_pk}")

            # Return user data as dict
            return user.to_dict()

    except ApiException as e:
        logger.error(f"API exception creating user: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        return None


async def add_user_to_group(user_pk: int, group_name: str = "Jellyfin Users") -> bool:
    """Add user to a group in Authentik."""
    try:
        configuration = _get_configuration()

        with authentik_client.ApiClient(configuration) as api_client:
            api = authentik_client.CoreApi(api_client)

            # Step 1: Get the group by name
            logger.info(f"Looking up group '{group_name}'...")
            groups_response = api.core_groups_list(search=group_name)

            # Find group with exact name match
            group = None
            for g in groups_response.results:
                if g.name.lower() == group_name.lower():
                    group = g
                    break

            if not group:
                logger.warning(f"Group '{group_name}' not found in Authentik")
                return False

            group_pk = group.pk
            logger.info(f"Found group '{group_name}' with pk={group_pk}")

            # Step 2: Check if user is already in group
            current_users = group.users or []
            logger.info(f"Current users in group: {current_users}")

            if user_pk in current_users:
                logger.info(f"User {user_pk} is already in group '{group_name}'")
                return True

            # Step 3: Add user to group
            logger.info(f"Adding user {user_pk} to group '{group_name}'...")
            user_account_request = UserAccountRequest(pk=user_pk)
            api.core_groups_add_user_create(group_pk, user_account_request)

            logger.info(f"Successfully added user {user_pk} to group '{group_name}'")
            return True

    except ApiException as e:
        logger.error(f"API exception adding user to group: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Error adding user to group: {str(e)}", exc_info=True)
        return False
