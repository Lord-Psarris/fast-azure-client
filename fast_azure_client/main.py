from typing import Optional

from furl import furl
from msal import ConfidentialClientApplication
from msal.authority import (AuthorityBuilder, AZURE_PUBLIC)

from .graph_utils import GraphAPI
from .fastapi_utils.auth_handler import AuthHandler


class AuthClient:
    """
    Client for handling authentication and authorization operations. \n

    This class provides methods for generating login URLs, validating authorization codes,
    authenticating with email and password, and obtaining utility objects for interacting
    with the Microsoft Graph API. \n

    Args:
        client_id (str): The client ID of the application. \n
        client_secret (str): The client secret of the application. \n
        tenant_id (str): The ID or Name of the Azure AD tenant. \n
        oauth_tenant_id (str, optional): The ID of the OAuth tenant. Defaults to None. \n
        authority (str, optional): The authority URL for authentication. Defaults to None. \n
        b2c_user_flow (str, optional): The user flow for B2C authentication. Defaults to None. \n
        redirect_url (str, optional): The redirect URL for authentication. Defaults to None. \n
        scopes (list, optional): The scopes to request during authentication. Defaults to []. \n
        mode (str, optional): The authentication mode (B2C or AD). Defaults to 'b2c'. \n

    """

    valid_auth_modes = ["b2c",  # b2c specifies the user is authenticating against an azure ad b2c setup
                        "ad"]  # ad for azure ad

    def __init__(
            self,
            client_id: str,
            client_secret: str,
            tenant_id: str,
            oauth_tenant_id: Optional[str] = None,
            authority: Optional[str] = None,
            b2c_user_flow: Optional[str] = None,
            redirect_url: Optional[str] = None,
            scopes: Optional[list] = None,
            mode: str = 'ad'
    ):
        # validate user provided mode
        if mode not in self.valid_auth_modes:
            raise ValueError(f"Invalid authentication mode. Supported modes: {', '.join(self.valid_auth_modes)}")

        # generate authority if no user provided value
        if authority is None:
            authority = self._generate_authority(mode, tenant_id, user_flow=b2c_user_flow)

        # set base variables
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.redirect_url = redirect_url
        self.client_secret = client_secret
        self.scopes = scopes if scopes else []
        self.oauth_tenant_id = oauth_tenant_id if oauth_tenant_id else tenant_id

        self.auth_session_data = {}  # used for storing config data for completing auth flows

        # initiate msal application
        self.app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority
        )

    def generate_auth_url(
            self,
            redirect_url: Optional[str] = None,
            scopes: Optional[list] = None,
            response_mode: str = 'query'
    ) -> str:
        """
        Generate an auth URL for initiating the authentication flow. \n

        Args:
            redirect_url (str, optional): The redirect URL for authentication. Defaults to None. \n
            scopes (list, optional): The scopes to request during authentication. Defaults to None. \n
            response_mode (str, optional): The type of response to expect. Defaults to 'query'. \n

        Returns:
            str: The generated auth URL. \n

        """
        # Update declared variables with new input
        self.redirect_url = redirect_url if redirect_url else self.redirect_url
        self.scopes = scopes if scopes else self.scopes

        # generate authentication url
        auth_data = self.app.initiate_auth_code_flow(self.scopes,
                                                     redirect_uri=self.redirect_url,
                                                     response_mode=response_mode
                                                     )
        self.auth_session_data[auth_data["state"]] = auth_data
        return auth_data.get("auth_uri")

    def validate_auth_response(self, auth_response: dict):
        """
        Validate the authorization response and obtain the access token. \n

        Args:
            auth_response (str): The query response returned from the auth process in dict form \n

        Returns:
            dict: The result of the authentication, including the access token. \n
        """

        # get auth data generated
        auth_data = self.auth_session_data[auth_response["state"]]

        # get the response data
        result = self.app.acquire_token_by_auth_code_flow(
            scopes=self.scopes,
            auth_code_flow=auth_data,
            auth_response=auth_response,
        )

        if "error" in result:
            raise Exception(f"error: {result['error']} :- {result.get('error_description', 'an error occurred')}")

        return result

    @staticmethod
    def parse_response_url(url: str) -> dict:
        """
        parses the returned url after completing the sign-on process, and return the query parameters as a dictionary
        """
        return dict(furl(url).args)

    def authenticate_email_password(self, email: str, password: str, scopes: list = None):
        """
        Authenticate using email and password. \n
        Note: This only works with the Azure AD flow. \n

        Args:
            email (str): The email address of the user. \n
            password (str): The password of the user. \n
            scopes (list, optional): The scopes to request during authentication. Defaults to []. \n

        Returns:
            str: The access token. \n

        Raises:
            Exception: If there is an error during authentication. \n

        """
        # Update declared variables with new input
        if scopes is not None:
            self.scopes = scopes

        result = self.app.acquire_token_by_username_password(email, password, scopes=self.scopes)

        if "error" in result:
            raise Exception(f"error: {result['error']} :- {result.get('error_description', 'an error occurred')}")

        return result

    def graph_utils(self, access_token: Optional[str] = None):
        """
        Get a utility object for interacting with the Microsoft Graph API. \n

        Args:
            access_token (str, optional): The access token to use. Defaults to None. \n

        Returns:
            GraphAPI: The GraphAPI object. \n

        """
        return GraphAPI(
            access_token,
            self.client_id,
            self.oauth_tenant_id,
            self.client_secret
        )

    def fastapi_auth_handler(self):
        """
        Get an authentication handler for FastAPI integration. \n

        Returns:
            AuthHandler: The AuthHandler object. \n

        """
        return AuthHandler(
            self.client_id,
            self.client_secret,
            self.oauth_tenant_id
        )

    @staticmethod
    def _generate_authority(mode: str, tenant_name: str, user_flow: Optional[str] = None):
        """
        Generate the authority URL based on the authentication mode and tenant details. \n

        Args:
            mode (str): The authentication mode ('b2c' or 'ad'). \n
            tenant_name (str): The name of the tenant. \n
            user_flow (str, optional): The user flow for B2C authentication. Defaults to None. \n

        Returns:
            str: The generated authority URL. \n

        """
        if mode == 'b2c' and user_flow:
            return f'https://{tenant_name}.b2clogin.com/{tenant_name}.onmicrosoft.com/{user_flow}'

        elif mode == 'ad':
            return AuthorityBuilder(AZURE_PUBLIC, tenant_name)
