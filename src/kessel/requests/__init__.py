import requests.auth
from kessel.auth import OAuth2ClientCredentials


class OAuth2Auth(requests.auth.AuthBase):
    def __init__(self, credentials: OAuth2ClientCredentials):
        """
        Args:
            credentials: The OAuth2ClientCredentials instance to use for auth.
        """
        self.credentials = credentials

    def __call__(self, r):
        """
        Apply OAuth2 auth to the request.

        This method is called automatically by requests to add auth
        headers to the request.

        Args:
            r: The request object to modify.

        Returns:
            The modified request object with auth headers.
        """
        # Get latest token
        token, _ = self.credentials.get_token()

        # Add Bearer token to the auth header
        r.headers["Authorization"] = f"Bearer {token}"

        return r


def oauth2_auth(credentials: OAuth2ClientCredentials) -> OAuth2Auth:
    """
    Create a requests-compatible OAuth2 auth handler.

    This function creates an auth handler that can be used with
    the requests library, similar to how oauth2_call_credentials creates
    gRPC call credentials.

    Args:
        credentials: An OAuth2ClientCredentials instance.

    Returns:
        OAuth2Auth: An auth handler that can be used with requests.
    """
    return OAuth2Auth(credentials)
