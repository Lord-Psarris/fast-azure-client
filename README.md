# FastAPI Azure Client

## Description

This package helps bridge integration between python (fastapi) applications and Microsoft Azure AD / AD B2C authentication flows

## Key Features

- Simple Sign Flow: The auth client can generate dynamic sign in urls, validate tokens and handle quiet sso flows.
- Fast API Auth Handler: Authentication handler for validating fastapi routes.
- Graph API Integration: MS Graph API integration to allow direct access to user information stored on azure.

## Installation

You can install the package using pip:

```shell
pip install --upgrade pip && pip install wheel

pip install git+https://github.com/Lord-Psarris/fast-azure-client.git
```

## Usage

For direct python integration, we can use the AuthClient class directly:
```python
from fast_azure_client import AuthClient

# for azure ad
client = AuthClient(client_id="<azure-app-registration-client-id>",
                    client_secret="<azure-app-registration-client-secret>", tenant_id="<azure-tenant-id>",
                    redirect_url="https://jwt.ms")

# for azure ad b2c
client = AuthClient(client_id='<azure-app-registration-client-id>',
                    client_secret='<azure-app-registration-client-secret>',
                    oauth_tenant_id="<azure-tenant-id>", tenant_id="<azure-tenant-name e.g default>",
                    b2c_user_flow="<azure-ad-b2c-user-flow-id>", scopes=['<scope-url>'],
                    redirect_url="https://jwt.ms", mode="b2c"
                    )

# generate the authentication url, and complete the sing-on process
print(client.generate_auth_url())

# grab the returned url after completing the sign-on process on web
response_url = ""  # return url with parameters after sign-on process
details = client.parse_response_url(response_url)
result = client.validate_auth_response(details)

# get token details
access_token = result["access_token"]
id_token = result["id_token"]

# for direct msal email flow  (note: this process is not advised)
result = client.authenticate_email_password(email='user@example.com', password='some_secure_password')
print(result)
```

For FastAPI integrations we can make use of the AuthHandler:
```python
from fastapi import FastAPI, Depends
from fast_azure_client import AuthClient
from fast_azure_client.fastapi_utils.auth_handler import AuthHandler

import configs  # config file with all environment variables and app configs

app = FastAPI(title='Auth Client API')

# setup client 
client = AuthClient(...)

# setup auth handler for application
auth_handler = client.fastapi_auth_handler()
# auth_handler = AuthHandler(configs.CLIENT_ID, configs.CLIENT_SECRET, configs.TENANT_ID)  note: this also works if the configs are different


# create login link
@app.get('/login')
def get_login_link():
    return client.generate_auth_url(redirect_url=configs.REDIRECT_URI)


# verify generated code
@app.get('/get-token')
def verify_token(response_details: dict): 
    result = client.validate_auth_response(response_details)
    return result["access_token"]  # returning token


# use auth handler in router
@app.get('/protected')
def this_is_protected(user: auth_handler.auth_wrapper = Depends()):
    return user
```

## Contributing

We welcome contributions to improve the application. To contribute, follow these steps:

- Fork the repository and create your branch:
```bash
git checkout -b feature/your-feature-name
```

-Make your changes and commit them:
```bash
git commit -m "Add your message here"
```

-Push to your branch:
```bash
git push origin feature/your-feature-name
```

-Finally, create a pull request on GitHub.

## Issues and Bug Reports

If you encounter any issues or bugs with the application, please open a new issue on this repository.

## License

...
