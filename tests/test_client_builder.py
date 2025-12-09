import pytest
from unittest.mock import Mock, patch

from kessel.inventory import ClientBuilder


class TestClientBuilderConstructor:
    def test_valid_target_string(self):
        """Test that a valid target string is accepted."""
        builder = ClientBuilder("localhost:8080")
        assert builder._target == "localhost:8080"
        assert builder._call_credentials is None
        assert builder._channel_credentials is None

    def test_empty_target_raises(self):
        """Test that empty target raises an error."""
        with pytest.raises(TypeError):
            ClientBuilder("")

    def test_none_target_raises(self):
        """Test that None target raises an error."""
        with pytest.raises(TypeError):
            ClientBuilder(None)

    def test_non_string_target_raises(self):
        """Test that non-string target raises an error."""
        with pytest.raises(TypeError):
            ClientBuilder(12345)


class TestClientBuilderInsecure:
    @patch("kessel.inventory.insecure_channel_credentials")
    def test_insecure_sets_channel_credentials(self, mock_insecure_creds):
        """Test that insecure() sets insecure channel credentials."""
        mock_creds = Mock()
        mock_insecure_creds.return_value = mock_creds

        builder = ClientBuilder("localhost:8080")
        builder.insecure()

        assert builder._channel_credentials == mock_creds
        mock_insecure_creds.assert_called()

    def test_insecure_clears_call_credentials(self):
        """Test that insecure() clears call credentials."""
        builder = ClientBuilder("localhost:8080")
        builder._call_credentials = Mock() 
        builder.insecure()

        assert builder._call_credentials is None

    def test_insecure_returns_self(self):
        """Test that insecure() returns self for method chaining."""
        builder = ClientBuilder("localhost:8080")
        result = builder.insecure()

        assert result is builder


class TestClientBuilderUnauthenticated:
    """Test ClientBuilder.unauthenticated() method."""

    def test_unauthenticated_clears_call_credentials(self):
        """Test that unauthenticated() clears call credentials."""
        builder = ClientBuilder("localhost:8080")
        builder._call_credentials = Mock() 
        builder.unauthenticated()

        assert builder._call_credentials is None

    def test_unauthenticated_sets_channel_credentials(self):
        """Test that unauthenticated() sets channel credentials when provided."""
        builder = ClientBuilder("localhost:8080")
        mock_channel_creds = Mock()
        builder.unauthenticated(channel_credentials=mock_channel_creds)

        assert builder._channel_credentials == mock_channel_creds

    def test_unauthenticated_returns_self(self):
        """Test that unauthenticated() returns self for method chaining."""
        builder = ClientBuilder("localhost:8080")
        result = builder.unauthenticated()

        assert result is builder


class TestClientBuilderAuthenticated:
    def test_authenticated_sets_call_credentials(self):
        """Test that authenticated() sets call credentials."""
        builder = ClientBuilder("localhost:8080")
        mock_call_creds = Mock()
        builder.authenticated(call_credentials=mock_call_creds)

        assert builder._call_credentials == mock_call_creds

    def test_authenticated_sets_channel_credentials(self):
        """Test that authenticated() sets channel credentials."""
        builder = ClientBuilder("localhost:8080")
        mock_channel_creds = Mock()
        builder.authenticated(channel_credentials=mock_channel_creds)

        assert builder._channel_credentials == mock_channel_creds

    def test_authenticated_sets_both_credentials(self):
        """Test that authenticated() sets both call and channel credentials."""
        builder = ClientBuilder("localhost:8080")
        mock_call_creds = Mock()
        mock_channel_creds = Mock()
        builder.authenticated(
            call_credentials=mock_call_creds, channel_credentials=mock_channel_creds
        )

        assert builder._call_credentials == mock_call_creds
        assert builder._channel_credentials == mock_channel_creds

    def test_authenticated_returns_self(self):
        """Test that authenticated() returns self for method chaining."""
        builder = ClientBuilder("localhost:8080")
        result = builder.authenticated()

        assert result is builder


class TestClientBuilderOAuth2ClientAuthenticated:
    @patch("kessel.inventory.oauth2_call_credentials")
    def test_oauth2_client_authenticated_sets_call_credentials(
        self, mock_oauth2_call_creds
    ):
        """Test that oauth2_client_authenticated() sets OAuth2 call credentials."""
        mock_creds = Mock()
        mock_oauth2_call_creds.return_value = mock_creds
        mock_oauth2_client = Mock()

        builder = ClientBuilder("localhost:8080")
        builder.oauth2_client_authenticated(mock_oauth2_client)

        mock_oauth2_call_creds.assert_called_once_with(mock_oauth2_client)
        assert builder._call_credentials == mock_creds

    @patch("kessel.inventory.oauth2_call_credentials")
    def test_oauth2_client_authenticated_sets_channel_credentials(
        self, mock_oauth2_call_creds
    ):
        """Test that oauth2_client_authenticated() sets channel credentials."""
        mock_oauth2_call_creds.return_value = Mock()
        mock_oauth2_client = Mock()
        mock_channel_creds = Mock()

        builder = ClientBuilder("localhost:8080")
        builder.oauth2_client_authenticated(
            mock_oauth2_client, channel_credentials=mock_channel_creds
        )

        assert builder._channel_credentials == mock_channel_creds

    @patch("kessel.inventory.oauth2_call_credentials")
    def test_oauth2_client_authenticated_returns_self(self, mock_oauth2_call_creds):
        """Test that oauth2_client_authenticated() returns self for method chaining."""
        mock_oauth2_call_creds.return_value = Mock()

        builder = ClientBuilder("localhost:8080")
        result = builder.oauth2_client_authenticated(Mock())

        assert result is builder


class TestClientBuilderCredentialValidation:
    @patch("kessel.inventory.oauth2_call_credentials")
    @patch("kessel.inventory.insecure_channel_credentials")
    def test_validate_credentials_raises_on_auth_with_insecure(
        self, mock_insecure_creds, mock_oauth2_call_creds
    ):
        """Test that validation raises when authenticating with insecure channel."""
        mock_insecure = Mock()
        mock_insecure_creds.return_value = mock_insecure
        mock_oauth2_call_creds.return_value = Mock()

        builder = ClientBuilder("localhost:8080")

        with pytest.raises(TypeError):
            builder.oauth2_client_authenticated(Mock(), channel_credentials=mock_insecure)
