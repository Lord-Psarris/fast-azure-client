from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Security
from functools import wraps

from ..graph_utils import GraphAPI
from .token_validators import decode_token


class AuthHandler:
    """
    Authentication handler for validating tokens and retrieving user details.

    This class provides methods to handle token authentication and user details retrieval
    using the Azure Active Directory B2C service.

    Args:
        client_id (str): The client ID of the application.
        client_secret (str): The client secret of the application.
        tenant_id (str): The ID of the Azure AD tenant.

    Attributes:
        security (HTTPBearer): The security scheme for bearer tokens.

    """

    security = HTTPBearer()

    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id

    def auth_wrapper(self, auth: HTTPAuthorizationCredentials = Security(security)):
        """
        Authentication wrapper for handling token verification and user details retrieval from azure.

        Args:
            auth (HTTPAuthorizationCredentials): The authorization credentials provided.

        Returns:
            dict: User details retrieved from the Graph API.

        """
        valid_token_data = decode_token(auth.credentials, client_id=self.client_id)
        unique_name = valid_token_data.get('preferred_username')
        emails = valid_token_data.get('emails', [None])

        email = unique_name if unique_name else emails[0]

        # Setup Graph API
        graph_api = GraphAPI(
            client_id=self.client_id,
            client_secret=self.client_secret,
            tenant_id=self.tenant_id
        )

        user = graph_api.get_user_details(email=email, given_name=valid_token_data.get("name"))
        return user
