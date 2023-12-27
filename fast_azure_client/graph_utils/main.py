from typing import Optional

from . import configs

import requests
import base64


class GraphAPI:

    def __init__(self, access_token: Optional[str] = None, client_id: Optional[str] = None,
                 tenant_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Class for interacting with Microsoft Graph API.

        Args:
            access_token (str, optional): Access token for API authentication. Defaults to None.
            client_id (str, optional): Client ID for API authentication. Defaults to None.
            tenant_id (str, optional): Tenant ID for API authentication. Defaults to None.
            client_secret (str, optional): Client secret for API authentication. Defaults to None.
        """

        self.client_secret = client_secret
        self.client_id = client_id
        self.tenant_id = tenant_id

        if not access_token:
            access_token = self._get_graph_api_access_token()

        # define base headers
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # set access token to class
        self.access_token = access_token

    def get_user_details(self, email: str = None, object_id: str = None, given_name: str = None) -> dict:
        # parse given name
        given_name = given_name if not given_name else given_name.lower()

        # get user details directly using object id
        if object_id:
            response = requests.get(f'{configs.user_list_url}/{object_id}',
                                    headers=self.headers)
            response.raise_for_status()

            return response.json()

        # get all users and filter by email
        else:
            response = requests.get(configs.user_list_url,
                                    headers=self.headers)
            response.raise_for_status()

            data = response.json()
            user_list = data["value"]

            # get the first user with expected email from a filtered list
            filtered_list = list(filter(lambda x: x["mail"] == email or str(x["givenName"]).lower() == given_name,
                                        user_list))
            user = next(iter(filtered_list), None)
            return user

    def update_user_details(self, object_id: str, requested_updates: dict) -> dict:
        """
        Update user details in Microsoft Graph API.

        Args:
            object_id (str): User's object ID.
            requested_updates (dict): Requested updates to user details.

        Returns:
            dict: Updated user details.

        """

        response = requests.patch(f'{configs.user_list_url}/{object_id}',
                                  json=requested_updates, headers=self.headers)
        print(response.json())
        response.raise_for_status()

        return response.json()

    def get_user_profile(self, object_id: str) -> str:
        """
        Get user profile image from Microsoft Graph API.

        Args:
            object_id (str): User's object ID.

        Returns:
            str: Base64 encoded image string.

        """
        # define headers
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # get new image from ms graph
        response = requests.get(f'{configs.user_list_url}/{object_id}/photo/$value',
                                headers=headers)

        # verify the user has a profile details
        if response.status_code == 404:
            return None

        # raise error for other cases
        response.raise_for_status()

        # parse response and get data
        data = response.content
        encoded_image_data = base64.b64encode(data).decode('utf-8')

        image_string = "data:image/png;base64," + encoded_image_data
        return image_string

    def update_user_profile(self, object_id: str, file_data: bytes, content_type: str = "image/png"):
        """
        Update user profile image in Microsoft Graph API.

        Args:
            object_id (str): User's object ID.
            file_data (bytes): Binary data of the new profile image.
            content_type (str, optional): Content type of the profile image. Defaults to "image/png".

        Returns:
            None

        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": content_type
        }

        # Post new image to Microsoft Graph API
        response = requests.put(f'{configs.user_list_url}/{object_id}/photo/$value',
                                data=file_data, headers=headers)
        response.raise_for_status()

    def create_user_on_azure(self, user_data: dict) -> dict:
        """
        Creates a user on Azure Active Directory using the Microsoft Graph API.

        Args:
            user_data (dict): User data including properties required for user creation.

        Returns:
            dict: User object representing the created user.

        Raises:
            requests.HTTPError: If the API request fails.

        Example:
            Example usage to create a user:

            >>> user_data = {
            ...     "accountEnabled": True,
            ...     "displayName": "Adele Vance",
            ...     "mailNickname": "AdeleV",
            ...     "userPrincipalName": "AdeleV@contoso.onmicrosoft.com",
            ...     "passwordProfile": {
            ...         "forceChangePasswordNextSignIn": True,
            ...         "password": "xWwvJ]6NMw+bWH-d"
            ...     }
            ... }

            >>> api = GraphAPI(access_token, client_id, tenant_id, client_secret)
            >>> response = api.create_user_on_azure(user_data)
            >>> print(response)
            {
                "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users/$entity",
                "id": "87d349ed-44d7-43e1-9a83-5f2406dee5bd",
                "businessPhones": [],
                "displayName": "Adele Vance",
                "givenName": "Adele",
                "jobTitle": "Product Marketing Manager",
                "mail": "AdeleV@contoso.onmicrosoft.com",
                "mobilePhone": "+1 425 555 0109",
                "officeLocation": "18/2111",
                "preferredLanguage": "en-US",
                "surname": "Vance",
                "userPrincipalName": "AdeleV@contoso.onmicrosoft.com"
            }
        """
        response = requests.post(configs.user_list_url, json=user_data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_new_user_fields(self, custom_fields: dict):
        """
        Adds custom data to Microsoft Graph for a user.

        Args:
            custom_fields (dict): A dictionary containing the custom data to add.

        Raises:
            requests.HTTPError: If the API request fails.

        Example:
            >>> data = {
            ...     "name": "jobGroupTracker",
            ...     "dataType": "String",
            ... }

            >>> api = GraphAPI(access_token, client_id, tenant_id, client_secret)
            >>> response = api.create_new_user_fields(data)
            >>> print(response)

        Notes:
            For more info visit this endpoint for more info
            https://learn.microsoft.com/en-us/graph/extensibility-open-users?tabs=http
        """
        # update custom_fields
        custom_fields["targetObjects"] = ["User"]

        # handle response
        response = requests.post(f'{configs.application_list_url}/extensionProperties',
                                 json=custom_fields, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def _get_graph_api_access_token(self):
        """
        Retrieve the access token for Microsoft Graph API using client credentials.

        Returns:
            str: Access token for Microsoft Graph API.

        Raises:
            HTTPError: If there's an error in the request or response.

        """
        request_data = {
            "client_id": self.client_id,
            "scope": "https://graph.microsoft.com/.default",
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

        response = requests.post(url, data=request_data, headers=headers)
        response.raise_for_status()

        token_data = response.json()
        return token_data["access_token"]

