"""Authentik API service module."""

import logging
import io
import qrcode
import requests
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

            # Return user data as dict with pk included
            user_dict = user.to_dict() if hasattr(user, 'to_dict') else {}
            user_dict['pk'] = user_pk
            return user_dict

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


async def enroll_totp(username: str, password: str) -> dict | None:
    """
    Enroll TOTP for a user by executing the enrollment flow.
    Returns dict with 'config_url' and 'qr_code' (bytes) or None on failure.
    """
    try:
        session = requests.Session()

        # Step 1: Initiate the TOTP enrollment flow
        logger.info(f"Initiating TOTP enrollment flow for user {username}...")
        flow_url = f"{AUTHENTIK_URL}/api/v3/flows/executor/default-authenticator-totp-setup/"

        # Get the initial challenge
        response = session.get(flow_url, timeout=10)

        if response.status_code != 200:
            logger.error(f"Failed to initiate TOTP flow: {response.status_code} - {response.text}")
            return None

        challenge_data = response.json()
        logger.info(f"Flow initiated. Challenge type: {challenge_data.get('type')}")

        # Step 2: Check if we need to authenticate first
        component = challenge_data.get('component', '')

        if 'identification' in component.lower():
            # Need to authenticate
            logger.info("Authenticating user for TOTP enrollment...")
            auth_response = session.post(
                flow_url,
                json={
                    'component': component,
                    'uid_field': username,
                    'password': password
                },
                timeout=10
            )

            if auth_response.status_code != 200:
                logger.error(f"Authentication failed: {auth_response.status_code} - {auth_response.text}")
                return None

            challenge_data = auth_response.json()
            logger.info(f"Authenticated. New component: {challenge_data.get('component')}")

        # Step 3: Look for TOTP stage response
        # The challenge should now contain the config_url
        if 'config_url' in challenge_data:
            config_url = challenge_data['config_url']
            logger.info(f"Received TOTP config URL")

            # Generate QR code
            qr_code_bytes = generate_qr_code(config_url)

            return {
                'config_url': config_url,
                'qr_code': qr_code_bytes
            }
        else:
            logger.error(f"config_url not found in response. Component: {challenge_data.get('component')}")
            logger.debug(f"Full response: {challenge_data}")
            return None

    except Exception as e:
        logger.error(f"Error enrolling TOTP: {str(e)}", exc_info=True)
        return None


def generate_qr_code(data: str) -> bytes:
    """
    Generate a QR code image from the given data.
    Returns the QR code as PNG bytes.
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        return img_bytes.getvalue()

    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}", exc_info=True)
        return None
