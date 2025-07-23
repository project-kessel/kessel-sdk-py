import datetime

import google.auth.credentials
import google.auth.transport.requests
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


class ClientCredentials(google.auth.credentials.Credentials):
    """
    Client credentials class for handling the OAuth 2.0 Client Credentials flow.

    Integrates with the google-auth and requests-oauthlib library to fetch an access token
    from a specified issuer url with automatic refreshing.
    """

    def __init__(
        self,
        issuer_url: str,
        client_id: str,
        client_secret: str,
    ):
        """
        Initializes the ClientCredentials.

        Args:
            issuer_url: The issuer URL of the OAuth 2.0 provider.
            client_id: The client ID for the application.
            client_secret: The client secret for the application.
        """
        super().__init__()
        self._issuer_url = issuer_url
        self._client_id = client_id
        self._client_secret = client_secret

        self._token_url = self._discover_token_endpoint(issuer_url)

        client = BackendApplicationClient(client_id=self._client_id)

        self._session = OAuth2Session(client=client)

        self.token = None
        self.expiry = None

    def _discover_token_endpoint(self, issuer_url: str) -> str:
        """
        Discovers the token endpoint from the OIDC provider's discovery document.

        Args:
            issuer_url: The base URL of the OIDC provider.

        Returns:
            The URL of the token endpoint.
        """
        discovery_url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
        try:
            response = requests.get(discovery_url, timeout=10)
            response.raise_for_status()
            config = response.json()
            token_endpoint = config.get("token_endpoint")
            if not token_endpoint:
                raise ValueError("'token_endpoint' not found in OIDC discovery document")

            return token_endpoint
        except requests.exceptions.RequestException as e:
            raise IOError(f"Failed to retrieve OIDC discovery document from {discovery_url}") from e
        except (ValueError, KeyError) as e:
            raise ValueError("Failed to parse OIDC discovery document or find 'token_endpoint'") from e

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
        self.expiry = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
