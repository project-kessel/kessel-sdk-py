import pytest
from unittest.mock import Mock, patch

from kessel.inventory import ClientBuilder, _DEFAULT_KEEPALIVE_OPTIONS


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
    def test_oauth2_client_authenticated_sets_call_credentials(self, mock_oauth2_call_creds):
        """Test that oauth2_client_authenticated() sets OAuth2 call credentials."""
        mock_creds = Mock()
        mock_oauth2_call_creds.return_value = mock_creds
        mock_oauth2_client = Mock()

        builder = ClientBuilder("localhost:8080")
        builder.oauth2_client_authenticated(mock_oauth2_client)

        mock_oauth2_call_creds.assert_called_once_with(mock_oauth2_client)
        assert builder._call_credentials == mock_creds

    @patch("kessel.inventory.oauth2_call_credentials")
    def test_oauth2_client_authenticated_sets_channel_credentials(self, mock_oauth2_call_creds):
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

        with pytest.raises(ValueError):
            builder.oauth2_client_authenticated(Mock(), channel_credentials=mock_insecure)


class TestClientBuilderChannelOptions:
    """Test ClientBuilder.channel_options() method."""

    def test_channel_options_returns_self(self):
        """Test that channel_options() returns self for method chaining."""
        builder = ClientBuilder("localhost:8080")
        result = builder.channel_options([("grpc.keepalive_time_ms", 30_000)])
        assert result is builder

    def test_channel_options_stores_user_options(self):
        """Test that channel_options() stores the provided options."""
        builder = ClientBuilder("localhost:8080")
        opts = [("grpc.keepalive_time_ms", 30_000)]
        builder.channel_options(opts)
        assert builder._user_channel_options == opts

    def test_channel_options_copies_input_list(self):
        """Test that channel_options() copies the list to avoid mutation."""
        builder = ClientBuilder("localhost:8080")
        opts = [("grpc.keepalive_time_ms", 30_000)]
        builder.channel_options(opts)
        opts.append(("extra_key", 1))
        assert ("extra_key", 1) not in builder._user_channel_options

    def test_channel_options_default_is_none(self):
        """Test that _user_channel_options starts as None."""
        builder = ClientBuilder("localhost:8080")
        assert builder._user_channel_options is None


class TestBuildChannelOptions:
    """Test ClientBuilder._build_channel_options() merge logic."""

    def test_sync_includes_keepalive_defaults(self):
        """Test that sync build includes all keepalive defaults."""
        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=True))
        for key, value in _DEFAULT_KEEPALIVE_OPTIONS:
            assert options[key] == value

    def test_async_includes_keepalive_defaults(self):
        """Test that async build includes all keepalive defaults."""
        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=False))
        for key, value in _DEFAULT_KEEPALIVE_OPTIONS:
            assert options[key] == value

    def test_sync_includes_single_threaded_unary_stream(self):
        """Test that sync build includes SingleThreadedUnaryStream option."""
        from grpc.experimental import ChannelOptions

        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=True))
        assert options[ChannelOptions.SingleThreadedUnaryStream] == 1

    def test_async_excludes_single_threaded_unary_stream(self):
        """Test that async build does not include SingleThreadedUnaryStream."""
        from grpc.experimental import ChannelOptions

        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=False))
        assert ChannelOptions.SingleThreadedUnaryStream not in options

    def test_user_options_override_defaults(self):
        """Test that caller-supplied options override keepalive defaults."""
        builder = ClientBuilder("localhost:8080")
        builder.channel_options([("grpc.keepalive_time_ms", 20_000)])
        options = dict(builder._build_channel_options(sync=True))
        assert options["grpc.keepalive_time_ms"] == 20_000

    def test_user_options_add_new_keys(self):
        """Test that caller-supplied options can add new keys."""
        builder = ClientBuilder("localhost:8080")
        builder.channel_options([("grpc.max_receive_message_length", 1024)])
        options = dict(builder._build_channel_options(sync=True))
        assert options["grpc.max_receive_message_length"] == 1024
        # Keepalive defaults still present
        assert options["grpc.keepalive_time_ms"] == 45_000

    def test_user_options_override_single_threaded_unary_stream(self):
        """Test that caller can override SingleThreadedUnaryStream on sync."""
        from grpc.experimental import ChannelOptions

        builder = ClientBuilder("localhost:8080")
        builder.channel_options([(ChannelOptions.SingleThreadedUnaryStream, 0)])
        options = dict(builder._build_channel_options(sync=True))
        assert options[ChannelOptions.SingleThreadedUnaryStream] == 0

    def test_no_user_options_returns_defaults_only(self):
        """Test that without user options, only defaults are returned."""
        from grpc.experimental import ChannelOptions

        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=True))
        expected_keys = {k for k, _ in _DEFAULT_KEEPALIVE_OPTIONS}
        expected_keys.add(ChannelOptions.SingleThreadedUnaryStream)
        assert set(options.keys()) == expected_keys

    def test_keepalive_time_ms_value(self):
        """Test that keepalive_time_ms default is 45000."""
        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=False))
        assert options["grpc.keepalive_time_ms"] == 45_000

    def test_keepalive_timeout_ms_value(self):
        """Test that keepalive_timeout_ms default is 10000."""
        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=False))
        assert options["grpc.keepalive_timeout_ms"] == 10_000

    def test_keepalive_permit_without_calls_value(self):
        """Test that keepalive_permit_without_calls default is 1."""
        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=False))
        assert options["grpc.keepalive_permit_without_calls"] == 1

    def test_max_pings_without_data_value(self):
        """Test that http2.max_pings_without_data default is 0."""
        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=False))
        assert options["grpc.http2.max_pings_without_data"] == 0
