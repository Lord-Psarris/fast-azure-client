from fastapi import HTTPException

import base64
import time
import json
import jwt


def verify_token_not_expired(payload):
    """
    Verifies if the token has expired based on the expiration time in the payload.

    Args:
        payload (dict): The payload of the JWT token.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.

    """
    token_expiration_time: int = payload.get('exp', 0)
    current_time: int = int(time.time())

    if current_time >= token_expiration_time:
        raise jwt.ExpiredSignatureError


def verify_user_is_authorized_for_this_app(payload: dict, client_id: str):
    """
    Verifies if the user is authorized to use the application based on the client ID.

    Args:
        payload (dict): The payload of the JWT token.
        client_id (str): The ID of the client application.

    Raises:
        HTTPException: If the user is not authorized to use this application (status_code=401).

    """
    # get the application id be it from ad or b2c tokens
    token_application_id = payload.get('appid', payload.get('aud', 0))

    # verify the token's ID is the same as the client ID
    is_valid_token = token_application_id == client_id

    if not is_valid_token:
        raise HTTPException(status_code=401, detail='User is not authorized to use this application')


def parse_token(token: str) -> dict:
    """
    Parse Azure AD B2C token and return the decoded payload as a dictionary.

    Args:
        token (str): The token to parse.

    Returns:
        dict: The decoded payload as a dictionary.

    Raises:
        jwt.InvalidTokenError: If the token format is incorrect.

    """
    try:
        _, payload, _ = token.split('.')

        decoded_payload = base64.urlsafe_b64decode(payload + '===')
        decoded_payload_str = decoded_payload.decode('utf-8')

        return json.loads(decoded_payload_str)

    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise jwt.DecodeError("Failed to decode token payload") from e


def decode_token(token: str, client_id: str) -> dict:
    try:
        payload = parse_token(token)

        # verify token isn't expired
        verify_token_not_expired(payload)

        # verify token is for this application
        verify_user_is_authorized_for_this_app(payload, client_id)

        payload["access_token"] = token
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, detail='Signature has expired')

    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail='Invalid token')

