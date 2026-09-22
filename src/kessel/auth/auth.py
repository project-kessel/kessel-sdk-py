import datetime
import math
import random
import threading
import time
from urllib.parse import urlparse

import google.auth.credentials
import google.auth.transport.requests
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

_DEFAULT_RETRY_CONFIG = {
    "max_retries": 3,
    "base_delay": 0.5,
    "max_delay": 2.0,
    "jitter": "full",
}

_VALID_RETRY_KEYS = frozenset(_DEFAULT_RETRY_CONFIG)
_VALID_JITTER_VALUES = ("full", "none")


def _validate_retry_config(retry):
    """Validate and normalize retry configuration.

    Returns a new dict with defaults applied for any missing keys.

    Args:
        retry: Dict with retry options to validate.

    Returns:
        Validated config dict with all keys present.

    Raises:
        TypeError: If retry is not a dict.
        ValueError: If any option key is unknown or any value is invalid.
    """
    if not isinstance(retry, dict):
        raise TypeError("retry must be a dict")

    unknown = set(retry) - _VALID_RETRY_KEYS
    if unknown:
        raise ValueError(f"unknown retry option: {sorted(unknown)[0]!r}")

    config = {**_DEFAULT_RETRY_CONFIG, **retry}

    if (
        isinstance(config["max_retries"], bool)
        or not isinstance(config["max_retries"], int)
        or config["max_retries"] < 0
    ):
        raise ValueError("retry max_retries must be a non-negative integer")

    for key in ("base_delay", "max_delay"):
        val = config[key]
        if isinstance(val, bool) or not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(f"retry {key} must be a positive number")
        if isinstance(val, float) and not math.isfinite(val):
            raise ValueError(f"retry {key} must be finite")

    if config["jitter"] not in _VALID_JITTER_VALUES:
        raise ValueError("retry jitter must be 'full' or 'none'")

    return config


def _is_retryable_error(error, http_status):
    """Check whether a token fetch error is retryable.

    Connection errors and timeouts are always retryable. HTTP 429 (rate
    limited) and 5xx (server error) responses are retryable when the
    status code was captured from the response.

    Args:
        error: The exception raised during the token fetch.
        http_status: The HTTP status code from the response, or None.

    Returns:
        True if the error is retryable, False otherwise.
    """
    if isinstance(error, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return True

    if http_status is not None and (http_status == 429 or 500 <= http_status <= 599):
        return True

    return False


class RefreshTokenResponse:
    """
    Response object containing OAuth 2.0 token and expiration information.
    """

    def __init__(self, access_token: str, expires_at: datetime.datetime):
        """
        Initialize the RefreshTokenResponse.

        Args:
            access_token: OAuth 2.0 token
            expires_at: Token's expiration time
        """
        self.access_token = access_token
        self.expires_at = expires_at


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

    After fetching, validates that the discovery document's ``issuer`` field matches
    the configured *issuer_url* (with trailing-slash normalization) and that the
    ``token_endpoint`` uses HTTPS.

    Args:
        issuer_url: The base URL of the OIDC provider.

    Returns:
        OIDCDiscoveryMetadata containing the discovered endpoints.

    Raises:
        requests.exceptions.RequestException: If the discovery document cannot be retrieved.
        ValueError: If the response is not a JSON object, the issuer is missing or not a
            string, the issuer does not match, or the token endpoint does not use HTTPS
            or is missing a host.
    """
    discovery_url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
    response = requests.get(discovery_url, timeout=10)
    response.raise_for_status()
    config = response.json()

    if not isinstance(config, dict):
        raise ValueError("OIDC discovery document must be a JSON object")

    # Validate issuer matches the configured URL (trailing-slash normalization)
    discovered_issuer = config.get("issuer")
    if not isinstance(discovered_issuer, str):
        raise ValueError(f"OIDC discovery issuer must be a string, got {discovered_issuer!r}")
    if discovered_issuer.rstrip("/") != issuer_url.rstrip("/"):
        raise ValueError(
            f"OIDC discovery issuer mismatch: expected {issuer_url.rstrip('/')!r}, "
            f"got {discovered_issuer.rstrip('/')!r}"
        )

    # Validate token_endpoint uses HTTPS
    token_endpoint = config.get("token_endpoint", "")
    parsed = urlparse(token_endpoint)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(
            f"OIDC discovery token_endpoint must use HTTPS and include a host, "
            f"got {token_endpoint!r}"
        )

    return OIDCDiscoveryMetadata(config)


class OAuth2ClientCredentials:
    """
    OAuth2ClientCredentials class for handling the OAuth 2.0 Client Credentials flow.

    Integrates with the google-auth and requests-oauthlib library to fetch an access token
    from a specified token endpoint with automatic refreshing.

    This class only accepts a direct token URL. For OIDC discovery, use the
    fetch_oidc_discovery function to obtain the token endpoint first.

    Token endpoint requests retry transient connection and timeout errors, HTTP
    429 responses, and HTTP 5xx responses with bounded exponential backoff and
    jitter. Other errors are returned without retrying.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_endpoint: str,
        *,
        retry=None,
    ):
        """
        Initializes the OAuth2ClientCredentials.

        Args:
            client_id: The client ID for the application.
            client_secret: The client secret for the application.
            token_endpoint: The direct token endpoint URL.
            retry: Optional dict of retry settings for token endpoint requests.
                Keys: ``max_retries`` (non-negative int, default 3; 0 disables),
                ``base_delay`` (positive number in seconds, default 0.5),
                ``max_delay`` (positive number in seconds, default 2.0),
                ``jitter`` (``'full'`` or ``'none'``, default ``'full'``).

        Raises:
            TypeError: If retry is not a dict.
            ValueError: If retry contains unknown keys or invalid values.
        """
        self._retry_config = _validate_retry_config(retry if retry is not None else {})
        self._token_endpoint = token_endpoint
        self._client_id = client_id
        self._client_secret = client_secret

        client = BackendApplicationClient(client_id=self._client_id)
        self._session = OAuth2Session(client=client)

        self._token = None
        self._expiry = None
        self._lock = threading.Lock()
        self._generation = 0

    def _needs_refresh(self) -> bool:
        current_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        return (
            self._token is None
            or self._expiry is None
            or self._expiry <= current_time + datetime.timedelta(seconds=300)
        )

    def get_token(self, force_refresh: bool = False) -> RefreshTokenResponse:
        """
        Get a valid access token, refreshing if necessary or forced.

        Uses double-checked locking to ensure that concurrent callers
        coalesce into a single SSO token request per refresh cycle.

        Args:
            force_refresh: If True, forces token refresh regardless of expiry.

        Returns:
            RefreshTokenResponse object containing access_token and expires_at.
        """
        # Snapshot the generation before the lock so we can detect if another
        # thread refreshed while we were waiting. A changed generation means a
        # fresh token is already available, letting us skip the SSO call.
        generation = self._generation

        if not force_refresh and not self._needs_refresh():
            return RefreshTokenResponse(access_token=self._token, expires_at=self._expiry)

        with self._lock:
            # Another thread already refreshed while we waited — accept that token
            if self._generation != generation and not self._needs_refresh():
                return RefreshTokenResponse(access_token=self._token, expires_at=self._expiry)

            current_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            token_data = self._fetch_token_with_retries()

            self._token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 0)
            self._expiry = current_time + datetime.timedelta(seconds=expires_in)
            self._generation += 1

        return RefreshTokenResponse(access_token=self._token, expires_at=self._expiry)

    def _fetch_token_with_retries(self):
        """Fetch a token, retrying on transient failures.

        Retries connection errors, timeouts, HTTP 429, and HTTP 5xx responses
        with exponential backoff and optional jitter. A response hook captures
        the HTTP status code so that server errors are detected even when the
        OAuth library raises a generic exception.
        """
        max_retries = self._retry_config["max_retries"]
        fetch_kwargs = dict(
            token_url=self._token_endpoint,
            client_id=self._client_id,
            client_secret=self._client_secret,
        )

        if max_retries == 0:
            return self._session.fetch_token(**fetch_kwargs)

        last_status = [None]

        def capture_response(response, *args, **kwargs):
            last_status[0] = response.status_code
            return response

        original_hooks = list(self._session.hooks.get("response", []))
        self._session.hooks["response"] = [capture_response] + original_hooks

        try:
            retry_index = 0
            while True:
                last_status[0] = None
                try:
                    return self._session.fetch_token(**fetch_kwargs)
                except Exception as e:
                    if retry_index < max_retries and _is_retryable_error(e, last_status[0]):
                        time.sleep(self._retry_delay(retry_index))
                        retry_index += 1
                    else:
                        raise
        finally:
            self._session.hooks["response"] = original_hooks

    def _retry_delay(self, retry_index):
        """Calculate the delay in seconds for the given retry attempt.

        Uses exponential backoff capped at ``max_delay``. With ``jitter='full'``,
        the delay is randomized between 0 and the cap.
        """
        base = self._retry_config["base_delay"]
        max_delay = self._retry_config["max_delay"]
        # Guard against OverflowError when retry_index is very large:
        # compute the index at which 2**n would exceed max_delay/base,
        # and short-circuit to max_delay beyond that threshold.
        saturation_index = math.ceil(math.log2(max_delay) - math.log2(base))
        if retry_index >= saturation_index:
            cap = max_delay
        else:
            cap = base * (2**retry_index)

        if self._retry_config["jitter"] == "none":
            return cap

        return random.random() * cap


class GoogleOAuth2ClientCredentials(google.auth.credentials.Credentials):
    """
    Adapter class that implements google.auth.credentials.Credentials interface
    for OAuth2ClientCredentials.
    """

    def __init__(self, credentials: OAuth2ClientCredentials):
        """
        Initialize the credentials adapter.

        Args:
            credentials: The OAuth2ClientCredentials instance to adapt.
        """
        self._credentials = credentials
        super().__init__()

    @property
    def token(self) -> str:
        return self._credentials._token

    @token.setter
    def token(self, value: str) -> None:
        self._credentials._token = value

    @property
    def expiry(self) -> datetime.datetime:
        return self._credentials._expiry

    @expiry.setter
    def expiry(self, value: datetime.datetime) -> None:
        self._credentials._expiry = value

    def refresh(self, request: google.auth.transport.requests.Request) -> None:
        self._credentials.get_token(force_refresh=True)


class AuthRequest(requests.auth.AuthBase):
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
        token_response = self.credentials.get_token()

        # Add Bearer token to the auth header
        r.headers["Authorization"] = f"Bearer {token_response.access_token}"

        return r


def oauth2_auth_request(credentials: OAuth2ClientCredentials) -> requests.auth.AuthBase:
    """
    Create a requests-compatible OAuth2 auth handler.

    This function creates an auth handler that can be used with
    the requests library, similar to how oauth2_call_credentials creates
    gRPC call credentials.

    Args:
        credentials: An OAuth2ClientCredentials instance.

    Returns:
        AuthRequest: An auth handler that can be used with requests.
    """
    return AuthRequest(credentials)
