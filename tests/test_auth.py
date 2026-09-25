import datetime
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch

import pytest
import requests.exceptions
from requests.exceptions import HTTPError

from kessel.auth import (
    OAuth2ClientCredentials,
    GoogleOAuth2ClientCredentials,
    OIDCDiscoveryMetadata,
    fetch_oidc_discovery,
    oauth2_auth_request,
)
from kessel.auth.auth import (
    RefreshTokenResponse,
    AuthRequest,
    _validate_retry_config,
    _is_retryable_error,
)


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
        "issuer": "https://example.com",
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


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_issuer_mismatch(mock_get):
    """Test OIDC discovery rejects mismatched issuer."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "issuer": "https://evil.example.com",
        "token_endpoint": "https://evil.example.com/oauth/token",
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="OIDC discovery issuer mismatch"):
        fetch_oidc_discovery("https://example.com")


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_issuer_match_with_trailing_slash(mock_get):
    """Test OIDC discovery accepts matching issuer with trailing-slash difference."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "issuer": "https://example.com/",
        "token_endpoint": "https://example.com/oauth/token",
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    metadata = fetch_oidc_discovery("https://example.com")

    assert metadata.token_endpoint == "https://example.com/oauth/token"


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_issuer_match_both_trailing_slashes(mock_get):
    """Test OIDC discovery accepts matching issuer when both have trailing slashes."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "issuer": "https://example.com/",
        "token_endpoint": "https://example.com/oauth/token",
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    metadata = fetch_oidc_discovery("https://example.com/")

    assert metadata.token_endpoint == "https://example.com/oauth/token"


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_http_token_endpoint_rejected(mock_get):
    """Test OIDC discovery rejects HTTP token endpoint."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "issuer": "https://example.com",
        "token_endpoint": "http://example.com/oauth/token",
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="token_endpoint must use HTTPS and include a host"):
        fetch_oidc_discovery("https://example.com")


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_non_https_scheme_rejected(mock_get):
    """Test OIDC discovery rejects non-HTTPS token endpoint schemes like ftp."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "issuer": "https://example.com",
        "token_endpoint": "ftp://example.com/oauth/token",
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="token_endpoint must use HTTPS and include a host"):
        fetch_oidc_discovery("https://example.com")


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_empty_token_endpoint_rejected(mock_get):
    """Test OIDC discovery rejects missing token_endpoint."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "issuer": "https://example.com",
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="token_endpoint must use HTTPS and include a host"):
        fetch_oidc_discovery("https://example.com")


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_missing_issuer_rejected(mock_get):
    """Test OIDC discovery rejects missing issuer field."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "token_endpoint": "https://example.com/oauth/token",
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="issuer must be a string"):
        fetch_oidc_discovery("https://example.com")


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_non_dict_document_rejected(mock_get):
    """Test OIDC discovery rejects non-object discovery document (e.g. JSON array)."""
    mock_response = Mock()
    mock_response.json.return_value = ["not", "a", "dict"]
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="must be a JSON object"):
        fetch_oidc_discovery("https://example.com")


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_null_issuer_rejected(mock_get):
    """Test OIDC discovery rejects null issuer value."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "issuer": None,
        "token_endpoint": "https://example.com/oauth/token",
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="issuer must be a string"):
        fetch_oidc_discovery("https://example.com")


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_numeric_issuer_rejected(mock_get):
    """Test OIDC discovery rejects non-string issuer value."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "issuer": 12345,
        "token_endpoint": "https://example.com/oauth/token",
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="issuer must be a string"):
        fetch_oidc_discovery("https://example.com")


@patch("kessel.auth.auth.requests.get")
def test_fetch_oidc_discovery_https_no_host_rejected(mock_get):
    """Test OIDC discovery rejects HTTPS token endpoint without hostname."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "issuer": "https://example.com",
        "token_endpoint": "https:///oauth/token",
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="token_endpoint must use HTTPS and include a host"):
        fetch_oidc_discovery("https://example.com")


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


def test_get_token_sends_client_credentials_in_request_body():
    """Test get_token asks requests-oauthlib to put client credentials in the form body."""
    credentials = OAuth2ClientCredentials(
        "test-client-id", "test-secret", "https://example.com/token"
    )

    mock_token_data = {
        "access_token": "access-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    with patch.object(
        credentials._session, "fetch_token", return_value=mock_token_data
    ) as mock_fetch:
        credentials.get_token()

        mock_fetch.assert_called_once_with(
            token_url="https://example.com/token",
            client_id="test-client-id",
            client_secret="test-secret",
            include_client_id=True,
        )


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


def test_get_token_concurrent_refresh_calls_sso_once():
    """Test that concurrent get_token() calls result in exactly one SSO fetch."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    credentials._token = "expiring-token"
    credentials._expiry = datetime.datetime.now(datetime.timezone.utc).replace(
        tzinfo=None
    ) + datetime.timedelta(seconds=60)

    barrier = threading.Barrier(20)
    mock_token_data = {
        "access_token": "refreshed-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    # Simulate real SSO latency so threads have time to pile up
    def slow_fetch(*_args, **_kwargs):
        time.sleep(0.05)
        return mock_token_data

    original_fetch = Mock(side_effect=slow_fetch)

    with patch.object(credentials._session, "fetch_token", original_fetch):

        def call_get_token():
            barrier.wait()
            return credentials.get_token()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(call_get_token) for _ in range(20)]
            results = [f.result() for f in as_completed(futures)]

    assert original_fetch.call_count == 1
    for result in results:
        assert result.access_token == "refreshed-token"


def test_get_token_concurrent_force_refresh_calls_sso_once():
    """Test that concurrent force_refresh=True calls result in exactly one SSO fetch."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )

    credentials._token = "expiring-token"
    credentials._expiry = datetime.datetime.now(datetime.timezone.utc).replace(
        tzinfo=None
    ) + datetime.timedelta(seconds=60)

    barrier = threading.Barrier(20)
    mock_token_data = {
        "access_token": "force-refreshed-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    # Simulate real SSO latency so threads have time to pile up
    def slow_fetch(*_args, **_kwargs):
        time.sleep(0.05)
        return mock_token_data

    original_fetch = Mock(side_effect=slow_fetch)

    with patch.object(credentials._session, "fetch_token", original_fetch):

        def call_get_token():
            barrier.wait()
            return credentials.get_token(force_refresh=True)

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(call_get_token) for _ in range(20)]
            results = [f.result() for f in as_completed(futures)]

    assert original_fetch.call_count == 1
    for result in results:
        assert result.access_token == "force-refreshed-token"


# ---------------------------------------------------------------------------
# Retry configuration validation
# ---------------------------------------------------------------------------


def test_validate_retry_config_defaults():
    """Test _validate_retry_config returns full defaults for an empty dict."""
    config = _validate_retry_config({})
    assert config == {
        "max_retries": 3,
        "base_delay": 0.5,
        "max_delay": 2.0,
        "jitter": "full",
    }


def test_validate_retry_config_custom():
    """Test _validate_retry_config merges custom values with defaults."""
    config = _validate_retry_config({"max_retries": 5, "jitter": "none"})
    assert config["max_retries"] == 5
    assert config["jitter"] == "none"
    assert config["base_delay"] == 0.5
    assert config["max_delay"] == 2.0


def test_validate_retry_config_not_dict():
    """Test _validate_retry_config rejects non-dict input."""
    with pytest.raises(TypeError, match="retry must be a dict"):
        _validate_retry_config("not-a-dict")


@pytest.mark.parametrize(
    "invalid_retry",
    [
        {"unknown_key": 1},
        {"max_retries": -1},
        {"max_retries": 1.5},
        {"max_retries": None},
        {"base_delay": 0},
        {"base_delay": -0.1},
        {"base_delay": float("inf")},
        {"max_delay": 0},
        {"max_delay": -1},
        {"max_delay": float("nan")},
        {"jitter": "random"},
        {"jitter": None},
    ],
    ids=[
        "unknown_key",
        "negative_max_retries",
        "float_max_retries",
        "none_max_retries",
        "zero_base_delay",
        "negative_base_delay",
        "infinite_base_delay",
        "zero_max_delay",
        "negative_max_delay",
        "nan_max_delay",
        "invalid_jitter_string",
        "none_jitter",
    ],
)
def test_validate_retry_config_rejects_invalid(invalid_retry):
    """Test _validate_retry_config rejects various invalid configurations."""
    with pytest.raises((TypeError, ValueError)):
        _validate_retry_config(invalid_retry)


def test_validate_retry_config_integer_delays():
    """Test _validate_retry_config accepts integer delay values."""
    config = _validate_retry_config({"base_delay": 1, "max_delay": 5})
    assert config["base_delay"] == 1
    assert config["max_delay"] == 5


def test_validate_retry_config_rejects_boolean_max_retries():
    """Test _validate_retry_config rejects bool max_retries (bool is subclass of int)."""
    with pytest.raises(ValueError, match="max_retries must be a non-negative integer"):
        _validate_retry_config({"max_retries": True})

    with pytest.raises(ValueError, match="max_retries must be a non-negative integer"):
        _validate_retry_config({"max_retries": False})


@pytest.mark.parametrize("key", ["base_delay", "max_delay"])
def test_validate_retry_config_rejects_boolean_delays(key):
    """Test _validate_retry_config rejects bool delay values."""
    with pytest.raises(ValueError, match=f"retry {key} must be a positive number"):
        _validate_retry_config({key: True})


# ---------------------------------------------------------------------------
# Retryable error classification
# ---------------------------------------------------------------------------


def test_is_retryable_error_connection_error():
    """Test _is_retryable_error returns True for ConnectionError."""
    assert _is_retryable_error(requests.exceptions.ConnectionError(), None) is True


def test_is_retryable_error_timeout():
    """Test _is_retryable_error returns True for Timeout."""
    assert _is_retryable_error(requests.exceptions.Timeout(), None) is True


def test_is_retryable_error_http_429():
    """Test _is_retryable_error returns True for HTTP 429."""
    assert _is_retryable_error(Exception("rate limited"), 429) is True


@pytest.mark.parametrize("status", [500, 502, 503, 504, 599])
def test_is_retryable_error_http_5xx(status):
    """Test _is_retryable_error returns True for HTTP 5xx status codes."""
    assert _is_retryable_error(Exception("server error"), status) is True


def test_is_retryable_error_http_400_not_retryable():
    """Test _is_retryable_error returns False for HTTP 400."""
    assert _is_retryable_error(Exception("bad request"), 400) is False


def test_is_retryable_error_http_401_not_retryable():
    """Test _is_retryable_error returns False for HTTP 401."""
    assert _is_retryable_error(Exception("unauthorized"), 401) is False


def test_is_retryable_error_generic_exception_not_retryable():
    """Test _is_retryable_error returns False for generic exceptions without status."""
    assert _is_retryable_error(Exception("unknown"), None) is False


# ---------------------------------------------------------------------------
# Retry delay calculation
# ---------------------------------------------------------------------------


def test_retry_delay_no_jitter():
    """Test _retry_delay with jitter='none' returns deterministic exponential backoff."""
    credentials = OAuth2ClientCredentials(
        "test-client",
        "test-secret",
        "https://example.com/token",
        retry={"jitter": "none", "base_delay": 0.5, "max_delay": 2.0},
    )
    assert credentials._retry_delay(0) == 0.5
    assert credentials._retry_delay(1) == 1.0
    assert credentials._retry_delay(2) == 2.0
    assert credentials._retry_delay(3) == 2.0  # capped at max_delay


def test_retry_delay_full_jitter_within_bounds():
    """Test _retry_delay with jitter='full' returns value between 0 and cap."""
    credentials = OAuth2ClientCredentials(
        "test-client",
        "test-secret",
        "https://example.com/token",
        retry={"jitter": "full", "base_delay": 0.5, "max_delay": 2.0},
    )
    for retry_index in range(4):
        cap = min(2.0, 0.5 * (2**retry_index))
        for _ in range(50):
            delay = credentials._retry_delay(retry_index)
            assert 0 <= delay <= cap


def test_retry_delay_large_retry_index_no_overflow():
    """Test _retry_delay does not raise OverflowError for very large retry_index."""
    credentials = OAuth2ClientCredentials(
        "test-client",
        "test-secret",
        "https://example.com/token",
        retry={"max_retries": 2000, "base_delay": 0.5, "max_delay": 2.0, "jitter": "none"},
    )
    # retry_index=1024 would cause 2**1024 * 0.5 → OverflowError without guard
    assert credentials._retry_delay(1024) == 2.0
    assert credentials._retry_delay(2000) == 2.0


# ---------------------------------------------------------------------------
# Retry initialization
# ---------------------------------------------------------------------------


def test_default_retry_config_on_init():
    """Test OAuth2ClientCredentials uses default retry config when none is provided."""
    credentials = OAuth2ClientCredentials(
        "test-client", "test-secret", "https://example.com/token"
    )
    assert credentials._retry_config == {
        "max_retries": 3,
        "base_delay": 0.5,
        "max_delay": 2.0,
        "jitter": "full",
    }


def test_custom_retry_config_on_init():
    """Test OAuth2ClientCredentials accepts custom retry config."""
    credentials = OAuth2ClientCredentials(
        "test-client",
        "test-secret",
        "https://example.com/token",
        retry={"max_retries": 1, "base_delay": 0.25, "max_delay": 0.75, "jitter": "none"},
    )
    assert credentials._retry_config == {
        "max_retries": 1,
        "base_delay": 0.25,
        "max_delay": 0.75,
        "jitter": "none",
    }


def test_invalid_retry_config_on_init():
    """Test OAuth2ClientCredentials rejects invalid retry config at init time."""
    with pytest.raises(ValueError, match="unknown retry option"):
        OAuth2ClientCredentials(
            "test-client",
            "test-secret",
            "https://example.com/token",
            retry={"unknown": 1},
        )


# ---------------------------------------------------------------------------
# Retry behavior integration
# ---------------------------------------------------------------------------


def test_retry_on_connection_error():
    """Test get_token retries on ConnectionError and succeeds on later attempt."""
    credentials = OAuth2ClientCredentials(
        "test-client",
        "test-secret",
        "https://example.com/token",
        retry={"max_retries": 3, "jitter": "none"},
    )

    mock_token_data = {
        "access_token": "recovered-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }
    call_count = [0]

    def fail_then_succeed(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] <= 2:
            raise requests.exceptions.ConnectionError("connection refused")
        return mock_token_data

    with patch.object(credentials._session, "fetch_token", side_effect=fail_then_succeed):
        with patch("kessel.auth.auth.time.sleep") as mock_sleep:
            result = credentials.get_token()

    assert result.access_token == "recovered-token"
    assert call_count[0] == 3
    assert mock_sleep.call_count == 2


def test_retry_on_timeout():
    """Test get_token retries on Timeout and succeeds on later attempt."""
    credentials = OAuth2ClientCredentials(
        "test-client",
        "test-secret",
        "https://example.com/token",
        retry={"max_retries": 3, "jitter": "none"},
    )

    mock_token_data = {
        "access_token": "timeout-recovered",
        "token_type": "Bearer",
        "expires_in": 3600,
    }
    call_count = [0]

    def fail_then_succeed(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise requests.exceptions.Timeout("read timed out")
        return mock_token_data

    with patch.object(credentials._session, "fetch_token", side_effect=fail_then_succeed):
        with patch("kessel.auth.auth.time.sleep") as mock_sleep:
            result = credentials.get_token()

    assert result.access_token == "timeout-recovered"
    assert call_count[0] == 2
    assert mock_sleep.call_count == 1


def test_retry_exhausted_raises():
    """Test get_token raises after all retries are exhausted."""
    credentials = OAuth2ClientCredentials(
        "test-client",
        "test-secret",
        "https://example.com/token",
        retry={"max_retries": 2, "jitter": "none"},
    )

    call_count = [0]

    def always_fail(*args, **kwargs):
        call_count[0] += 1
        raise requests.exceptions.ConnectionError("connection refused")

    with patch.object(credentials._session, "fetch_token", side_effect=always_fail):
        with patch("kessel.auth.auth.time.sleep"):
            with pytest.raises(
                requests.exceptions.ConnectionError, match="connection refused"
            ):
                credentials.get_token()

    assert call_count[0] == 3  # 1 initial + 2 retries


def test_no_retry_on_permanent_error():
    """Test get_token does not retry on non-retryable errors."""
    credentials = OAuth2ClientCredentials(
        "test-client",
        "test-secret",
        "https://example.com/token",
        retry={"max_retries": 3},
    )

    call_count = [0]

    def permanent_fail(*args, **kwargs):
        call_count[0] += 1
        raise ValueError("invalid_grant")

    with patch.object(credentials._session, "fetch_token", side_effect=permanent_fail):
        with patch("kessel.auth.auth.time.sleep") as mock_sleep:
            with pytest.raises(ValueError, match="invalid_grant"):
                credentials.get_token()

    assert call_count[0] == 1
    mock_sleep.assert_not_called()


def test_retry_disabled_with_zero_max_retries():
    """Test get_token does not retry when max_retries=0."""
    credentials = OAuth2ClientCredentials(
        "test-client",
        "test-secret",
        "https://example.com/token",
        retry={"max_retries": 0},
    )

    call_count = [0]

    def fail_once(*args, **kwargs):
        call_count[0] += 1
        raise requests.exceptions.ConnectionError("connection refused")

    with patch.object(credentials._session, "fetch_token", side_effect=fail_once):
        with patch("kessel.auth.auth.time.sleep") as mock_sleep:
            with pytest.raises(requests.exceptions.ConnectionError):
                credentials.get_token()

    assert call_count[0] == 1
    mock_sleep.assert_not_called()


def test_retry_sleep_delay_values():
    """Test that retry sleeps with correct exponential backoff delays."""
    credentials = OAuth2ClientCredentials(
        "test-client",
        "test-secret",
        "https://example.com/token",
        retry={"max_retries": 3, "base_delay": 0.5, "max_delay": 2.0, "jitter": "none"},
    )

    def always_fail(*args, **kwargs):
        raise requests.exceptions.ConnectionError("connection refused")

    with patch.object(credentials._session, "fetch_token", side_effect=always_fail):
        with patch("kessel.auth.auth.time.sleep") as mock_sleep:
            with pytest.raises(requests.exceptions.ConnectionError):
                credentials.get_token()

    assert mock_sleep.call_count == 3
    assert mock_sleep.call_args_list[0][0][0] == 0.5
    assert mock_sleep.call_args_list[1][0][0] == 1.0
    assert mock_sleep.call_args_list[2][0][0] == 2.0


def test_retry_restores_session_hooks():
    """Test that retry logic restores original session hooks after completion."""
    credentials = OAuth2ClientCredentials(
        "test-client",
        "test-secret",
        "https://example.com/token",
        retry={"max_retries": 1},
    )

    original_hooks = list(credentials._session.hooks.get("response", []))

    def always_fail(*args, **kwargs):
        raise requests.exceptions.ConnectionError("connection refused")

    with patch.object(credentials._session, "fetch_token", side_effect=always_fail):
        with patch("kessel.auth.auth.time.sleep"):
            with pytest.raises(requests.exceptions.ConnectionError):
                credentials.get_token()

    assert credentials._session.hooks.get("response", []) == original_hooks
