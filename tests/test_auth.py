import pytest
import datetime
from unittest.mock import Mock, patch
from requests.exceptions import HTTPError

from kessel.auth import (
    OAuth2ClientCredentials,
    GoogleOAuth2ClientCredentials,
    OIDCDiscoveryMetadata,
    fetch_oidc_discovery,
    oauth2_auth_request,
)
from kessel.auth.auth import RefreshTokenResponse, AuthRequest


def test_oauth2_client_credentials_initialization():
    """Test that OAuth2ClientCredentials is properly initialized with all parameters."""
    client_id = "test-client-id"
    client_secret = "test-client-secret"
    token_endpoint = "https://example.com/token"

    credentials = OAuth2ClientCredentials(client_id, client_secret, token_endpoint)

    assert credentials._client_id == client_id
    assert credentials._client_secret == client_secret
    assert credentials._token_endpoint == token_endpoint
    assert credentials._token is None
    assert credentials._expiry is None
    assert credentials._session is not None


def test_refresh_token_response():
    """Test RefreshTokenResponse initialization."""
    access_token = "test-token"
    expires_at = datetime.datetime.now() + datetime.timedelta(hours=1)

    response = RefreshTokenResponse(access_token, expires_at)

    assert response.access_token == access_token
    assert response.expires_at == expires_at


def test_oidc_discovery_metadata():
    """Test OIDCDiscoveryMetadata initialization and token_endpoint property."""
    discovery_doc = {
        "token_endpoint": "https://example.com/oauth/token",
        "issuer": "https://example.com",
    }

    metadata = OIDCDiscoveryMetadata(discovery_doc)

    assert metadata.token_endpoint == "https://example.com/oauth/token"


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_success(mock_get):
    """Test successful OIDC discovery."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "token_endpoint": "https://example.com/oauth/token",
        "issuer": "https://example.com",
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    metadata = fetch_oidc_discovery("https://example.com")

    assert metadata.token_endpoint == "https://example.com/oauth/token"
    mock_get.assert_called_once_with(
        "https://example.com/.well-known/openid-configuration", timeout=10
    )


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_with_trailing_slash(mock_get):
    """Test OIDC discovery with trailing slash in issuer URL."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "token_endpoint": "https://example.com/oauth/token",
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    fetch_oidc_discovery("https://example.com/")

    mock_get.assert_called_once_with(
        "https://example.com/.well-known/openid-configuration", timeout=10
    )


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_http_error(mock_get):
    """Test OIDC discovery with HTTP error."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = HTTPError("Not Found")
    mock_get.return_value = mock_response

    with pytest.raises(HTTPError):
        fetch_oidc_discovery("https://invalid.example.com")


def test_get_token_initial_fetch():
    """Test get_token fetches token on first call."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    mock_token_data = {
        "access_token": "new-access-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    with patch.object(credentials._session, "fetch_token", return_value=mock_token_data):
        result = credentials.get_token()

        assert result.access_token == "new-access-token"
        assert result.expires_at > datetime.datetime.now()
        assert credentials._token == "new-access-token"


def test_get_token_uses_cached_token():
    """Test get_token returns cached token when still valid."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    credentials._token = "cached-token"
    credentials._expiry = datetime.datetime.now(datetime.timezone.utc).replace(
        tzinfo=None
    ) + datetime.timedelta(hours=1)

    with patch.object(credentials._session, "fetch_token") as mock_fetch:
        result = credentials.get_token()

        assert result.access_token == "cached-token"
        mock_fetch.assert_not_called()


def test_get_token_force_refresh():
    """Test get_token refreshes token when force_refresh is True."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    credentials._token = "old-token"
    credentials._expiry = datetime.datetime.now(datetime.timezone.utc).replace(
        tzinfo=None
    ) + datetime.timedelta(hours=1)

    mock_token_data = {
        "access_token": "refreshed-token",
        "token_type": "Bearer",
        "expires_in": 7200,
    }

    with patch.object(credentials._session, "fetch_token", return_value=mock_token_data):
        result = credentials.get_token(force_refresh=True)

        assert result.access_token == "refreshed-token"
        assert credentials._token == "refreshed-token"


def test_get_token_refreshes_expiring_soon():
    """Test get_token refreshes token when expiring within 300 seconds."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    credentials._token = "expiring-token"
    credentials._expiry = datetime.datetime.now(datetime.timezone.utc).replace(
        tzinfo=None
    ) + datetime.timedelta(minutes=2)

    mock_token_data = {
        "access_token": "fresh-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    with patch.object(credentials._session, "fetch_token", return_value=mock_token_data):
        result = credentials.get_token()

        assert result.access_token == "fresh-token"


def test_get_token_refreshes_expired():
    """Test get_token refreshes expired token."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    # Set up an expired token
    credentials._token = "expired-token"
    credentials._expiry = datetime.datetime.now(datetime.timezone.utc).replace(
        tzinfo=None
    ) - datetime.timedelta(hours=1)

    mock_token_data = {
        "access_token": "new-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    with patch.object(credentials._session, "fetch_token", return_value=mock_token_data):
        result = credentials.get_token()

        assert result.access_token == "new-token"


def test_get_token_default_expires_in():
    """Test get_token with missing expires_in (defaults to 0)."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    mock_token_data = {
        "access_token": "token-no-expiry",
        "token_type": "Bearer",
        # No expires_in field
    }

    with patch.object(credentials._session, "fetch_token", return_value=mock_token_data):
        result = credentials.get_token()

        assert result.access_token == "token-no-expiry"
        assert result.expires_at <= datetime.datetime.now(datetime.timezone.utc).replace(
            tzinfo=None
        ) + datetime.timedelta(seconds=1)


def test_get_token_server_error():
    """Test get_token handles server errors."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    with patch.object(
        credentials._session, "fetch_token", side_effect=Exception("Unauthorized")
    ):
        with pytest.raises(Exception) as exc_info:
            credentials.get_token()
        assert "Unauthorized" in str(exc_info.value)


def test_oauth2_auth_request():
    """Test oauth2_auth_request creates AuthRequest instance."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    auth_request = oauth2_auth_request(credentials)

    assert isinstance(auth_request, AuthRequest)
    assert auth_request.credentials == credentials


def test_auth_request_call_adds_bearer_token():
    """Test AuthRequest adds Bearer token to request headers."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    credentials._token = "test-access-token-123"
    credentials._expiry = datetime.datetime.now(datetime.timezone.utc).replace(
        tzinfo=None
    ) + datetime.timedelta(hours=1)

    auth_request = AuthRequest(credentials)

    mock_request = Mock()
    mock_request.headers = {}

    result = auth_request(mock_request)

    assert result.headers["Authorization"] == "Bearer test-access-token-123"
    assert result == mock_request


def test_auth_request_call_fetches_token():
    """Test AuthRequest fetches token when needed."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    mock_token_data = {
        "access_token": "fetched-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    with patch.object(credentials._session, "fetch_token", return_value=mock_token_data):
        auth_request = AuthRequest(credentials)

        mock_request = Mock()
        mock_request.headers = {}

        result = auth_request(mock_request)

        assert result.headers["Authorization"] == "Bearer fetched-token"


def test_auth_request_call_refreshes_expired_token():
    """Test AuthRequest refreshes expired token before adding to request."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    credentials._token = "expired-token"
    credentials._expiry = datetime.datetime.now(datetime.timezone.utc).replace(
        tzinfo=None
    ) - datetime.timedelta(hours=1)

    mock_token_data = {
        "access_token": "refreshed-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    with patch.object(credentials._session, "fetch_token", return_value=mock_token_data):
        auth_request = AuthRequest(credentials)

        mock_request = Mock()
        mock_request.headers = {}

        result = auth_request(mock_request)

        assert result.headers["Authorization"] == "Bearer refreshed-token"


def test_google_oauth2_adapter_initialization():
    """Test GoogleOAuth2ClientCredentials adapter initialization."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    adapter = GoogleOAuth2ClientCredentials(credentials)

    assert adapter._credentials == credentials


def test_google_oauth2_adapter_token_property():
    """Test GoogleOAuth2ClientCredentials token property getter and setter."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )
    
    adapter = GoogleOAuth2ClientCredentials(credentials)
    
    assert adapter.token is None
    
    adapter.token = "new-token"
    assert credentials._token == "new-token"
    
    credentials._token = "test-token"
    assert adapter.token == "test-token"

def test_google_oauth2_adapter_refresh():
    """Test GoogleOAuth2ClientCredentials refresh method."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    mock_token_data = {
        "access_token": "refreshed-via-adapter",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    with patch.object(credentials._session, "fetch_token", return_value=mock_token_data):
        adapter = GoogleOAuth2ClientCredentials(credentials)

        mock_request = Mock()

        adapter.refresh(mock_request)

        assert adapter.token == "refreshed-via-adapter"
        assert credentials._token == "refreshed-via-adapter"


def test_oauth2_client_credentials_with_none_token():
    """Test behavior when token is None."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    assert credentials._token is None
    assert credentials._expiry is None

    mock_token_data = {
        "access_token": "first-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    with patch.object(credentials._session, "fetch_token", return_value=mock_token_data):
        result = credentials.get_token()
        assert result.access_token == "first-token"


def test_token_with_zero_expires_in():
    """Test token refresh with zero expires_in."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    mock_token_data = {
        "access_token": "zero-expiry-token",
        "token_type": "Bearer",
        "expires_in": 0,
    }

    with patch.object(credentials._session, "fetch_token", return_value=mock_token_data):
        result = credentials.get_token()
        assert result.access_token == "zero-expiry-token"
        assert result.expires_at <= datetime.datetime.now(datetime.timezone.utc).replace(
            tzinfo=None
        ) + datetime.timedelta(seconds=1)
