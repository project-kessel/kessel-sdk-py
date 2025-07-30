import datetime

import google.auth.credentials
import google.auth.transport.requests
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


class OIDCDiscoveryMetadata:
    """
    Represents OIDC discovery metadata.
    """

    def __init__(self, discovery_document: dict):
        self._document = discovery_document

    @property
    def token_endpoint(self) -> str:
        return self._document["token_endpoint"]


def fetch_oidc_discovery(issuer_url: str) -> OIDCDiscoveryMetadata:
    """
    Fetches OIDC discovery metadata from the provider.

    This function makes a network request to the OIDC provider's discovery endpoint
    to retrieve the provider's metadata including the token endpoint.

    Args:
        issuer_url: The base URL of the OIDC provider.

    Returns:
        OIDCDiscoveryMetadata containing the discovered endpoints.

    Raises:
        requests.exceptions.RequestException: If the discovery document cannot be retrieved.
        ValueError: If the response is not valid JSON.
    """
    discovery_url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
    response = requests.get(discovery_url, timeout=10)
    response.raise_for_status()
    config = response.json()

    return OIDCDiscoveryMetadata(config)


class OAuth2ClientCredentials(google.auth.credentials.Credentials):
    """
    OAuth2ClientCredentials class for handling the OAuth 2.0 Client Credentials flow.

    Integrates with the google-auth and requests-oauthlib library to fetch an access token
    from a specified token endpoint with automatic refreshing.

    This class only accepts a direct token URL. For OIDC discovery, use the
    fetch_oidc_discovery function to obtain the token endpoint first.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
    ):
        """
        Initializes the OAuth2ClientCredentials.

        Args:
            client_id: The client ID for the application.
            client_secret: The client secret for the application.
            token_url: The direct token endpoint URL.
        """
        super().__init__()

        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret

        client = BackendApplicationClient(client_id=self._client_id)
        self._session = OAuth2Session(client=client)

        self.token = None
        self.expiry = None

    def refresh(self, request: google.auth.transport.requests.Request) -> None:
        """
        Refreshes the access token.

        This method is called automatically by google-auth
        when it determines the token is expired or missing.

        Args:
            request: A google-auth transport request object (not used in this flow, but required
            by the interface).
        """
        token_data = self._session.fetch_token(
            token_url=self._token_url,
            client_id=self._client_id,
            client_secret=self._client_secret,
        )

        self.token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 0)
        self.expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            seconds=expires_in
        )
