import datetime

import google.auth.credentials
import google.auth.transport.requests
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


class OIDCDiscovery:
    """
    OIDC Discovery class for discovering OAuth 2.0 endpoints from an OIDC provider.

    Handles the OIDC discovery process to find the token endpoint from the provider's discovery document.
    """

    def __init__(self, issuer_url: str):
        """
        Initializes the OIDCDiscovery.

        Args:
            issuer_url: The base URL of the OIDC provider.
        """
        self.issuer_url = issuer_url
        self._token_endpoint = None

    def fetch_oidc_discovery(self) -> str:
        """
        Fetches the OIDC discovery token endpoint.

        This method makes a network request to the OIDC provider's discovery endpoint.

        Returns:
            The URL of the token endpoint.
        """
        if self._token_endpoint is None:
            self._discover_token_endpoint()

        return self._token_endpoint

    def _discover_token_endpoint(self) -> None:
        """
        Discovers and caches the token endpoint from the OIDC discovery document.
        """
        discovery_url = f"{self.issuer_url.rstrip('/')}/.well-known/openid-configuration"
        try:
            response = requests.get(discovery_url, timeout=10)
            response.raise_for_status()
            config = response.json()
            token_endpoint = config.get("token_endpoint")
            if not token_endpoint:
                raise ValueError("'token_endpoint' not found in OIDC discovery document")

            self._token_endpoint = token_endpoint
        except requests.exceptions.RequestException as e:
            raise IOError(f"Failed to retrieve OIDC discovery document from {discovery_url}") from e
        except (ValueError, KeyError) as e:
            raise ValueError(
                "Failed to parse OIDC discovery document or find 'token_endpoint'"
            ) from e


class OAuth2ClientCredentials(google.auth.credentials.Credentials):
    """
    OAuth2ClientCredentials class for handling the OAuth 2.0 Client Credentials flow.

    Integrates with the google-auth and requests-oauthlib library to fetch an access token
    from a specified token endpoint with automatic refreshing.

    This class only accepts a direct token URL. For OIDC discovery, use the
    OIDCDiscovery class to obtain the token endpoint first.
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

        self._initialized = False
        self._session = None

        self.token = None
        self.expiry = None

    def initialize(self) -> None:
        """
        Initializes the OAuth2ClientCredentials.
        """
        if self._initialized:
            return

        client = BackendApplicationClient(client_id=self._client_id)
        self._session = OAuth2Session(client=client)

        self._initialized = True

    def refresh(self, request: google.auth.transport.requests.Request) -> None:
        """
        Refreshes the access token.

        This method is called automatically by google-auth
        when it determines the token is expired or missing.

        Args:
            request: A google-auth transport request object (not used in this flow, but required
            by the interface).
        """
        self.initialize()

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
