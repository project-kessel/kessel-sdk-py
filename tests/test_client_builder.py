from datetime import timedelta

import pytest
from unittest.mock import Mock, patch

from kessel.inventory import (
    ClientBuilder,
    _DEFAULT_KEEPALIVE_INTERVAL_MS,
    _DEFAULT_KEEPALIVE_TIMEOUT_MS,
    _DEFAULT_KEEPALIVE_PERMIT_WITHOUT_CALLS,
)


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


class TestKeepaliveMethod:
    """Test ClientBuilder.keepalive() typed fluent API."""

    def test_keepalive_returns_self(self):
        """Test that keepalive() returns self for method chaining."""
        builder = ClientBuilder("localhost:8080")
        result = builder.keepalive(interval=timedelta(seconds=30))
        assert result is builder

    def test_keepalive_sets_interval(self):
        """Test that keepalive() sets interval in milliseconds."""
        builder = ClientBuilder("localhost:8080")
        builder.keepalive(interval=timedelta(seconds=40))
        assert builder._keepalive_interval_ms == 40_000

    def test_keepalive_sets_timeout(self):
        """Test that keepalive() sets timeout in milliseconds."""
        builder = ClientBuilder("localhost:8080")
        builder.keepalive(timeout=timedelta(seconds=15))
        assert builder._keepalive_timeout_ms == 15_000

    def test_keepalive_sets_permit_without_calls(self):
        """Test that keepalive() sets permit_without_calls flag."""
        builder = ClientBuilder("localhost:8080")
        builder.keepalive(permit_without_calls=False)
        assert builder._keepalive_permit_without_calls is False

    def test_keepalive_omitted_values_retain_defaults(self):
        """Test that omitted values keep their defaults."""
        builder = ClientBuilder("localhost:8080")
        builder.keepalive(interval=timedelta(seconds=30))
        assert builder._keepalive_interval_ms == 30_000
        assert builder._keepalive_timeout_ms == _DEFAULT_KEEPALIVE_TIMEOUT_MS
        assert builder._keepalive_permit_without_calls == _DEFAULT_KEEPALIVE_PERMIT_WITHOUT_CALLS

    def test_keepalive_repeated_calls_update_only_supplied_fields(self):
        """Test that repeated keepalive() calls update only supplied fields."""
        builder = ClientBuilder("localhost:8080")
        builder.keepalive(interval=timedelta(seconds=30))
        builder.keepalive(timeout=timedelta(seconds=5))
        assert builder._keepalive_interval_ms == 30_000
        assert builder._keepalive_timeout_ms == 5_000
        assert builder._keepalive_permit_without_calls == _DEFAULT_KEEPALIVE_PERMIT_WITHOUT_CALLS

    def test_keepalive_all_fields_at_once(self):
        """Test that keepalive() can set all fields in a single call."""
        builder = ClientBuilder("localhost:8080")
        builder.keepalive(
            interval=timedelta(seconds=60),
            timeout=timedelta(seconds=20),
            permit_without_calls=False,
        )
        assert builder._keepalive_interval_ms == 60_000
        assert builder._keepalive_timeout_ms == 20_000
        assert builder._keepalive_permit_without_calls is False

    def test_keepalive_sub_second_interval(self):
        """Test that keepalive() handles sub-second timedelta correctly."""
        builder = ClientBuilder("localhost:8080")
        builder.keepalive(interval=timedelta(milliseconds=500))
        assert builder._keepalive_interval_ms == 500

    def test_keepalive_no_args_is_noop(self):
        """Test that keepalive() with no arguments is a no-op."""
        builder = ClientBuilder("localhost:8080")
        builder.keepalive()
        assert builder._keepalive_interval_ms == _DEFAULT_KEEPALIVE_INTERVAL_MS
        assert builder._keepalive_timeout_ms == _DEFAULT_KEEPALIVE_TIMEOUT_MS
        assert builder._keepalive_permit_without_calls == _DEFAULT_KEEPALIVE_PERMIT_WITHOUT_CALLS


class TestKeepaliveValidation:
    """Test keepalive() input validation."""

    def test_interval_non_timedelta_raises_type_error(self):
        """Test that non-timedelta interval raises TypeError."""
        builder = ClientBuilder("localhost:8080")
        with pytest.raises(TypeError, match="interval must be a timedelta"):
            builder.keepalive(interval=45)

    def test_timeout_non_timedelta_raises_type_error(self):
        """Test that non-timedelta timeout raises TypeError."""
        builder = ClientBuilder("localhost:8080")
        with pytest.raises(TypeError, match="timeout must be a timedelta"):
            builder.keepalive(timeout="10s")

    def test_permit_without_calls_non_bool_raises_type_error(self):
        """Test that non-bool permit_without_calls raises TypeError."""
        builder = ClientBuilder("localhost:8080")
        with pytest.raises(TypeError, match="permit_without_calls must be a bool"):
            builder.keepalive(permit_without_calls=1)

    def test_interval_zero_raises_value_error(self):
        """Test that zero interval raises ValueError."""
        builder = ClientBuilder("localhost:8080")
        with pytest.raises(ValueError, match="interval must be positive"):
            builder.keepalive(interval=timedelta(0))

    def test_interval_negative_raises_value_error(self):
        """Test that negative interval raises ValueError."""
        builder = ClientBuilder("localhost:8080")
        with pytest.raises(ValueError, match="interval must be positive"):
            builder.keepalive(interval=timedelta(seconds=-1))

    def test_timeout_zero_raises_value_error(self):
        """Test that zero timeout raises ValueError."""
        builder = ClientBuilder("localhost:8080")
        with pytest.raises(ValueError, match="timeout must be positive"):
            builder.keepalive(timeout=timedelta(0))

    def test_timeout_negative_raises_value_error(self):
        """Test that negative timeout raises ValueError."""
        builder = ClientBuilder("localhost:8080")
        with pytest.raises(ValueError, match="timeout must be positive"):
            builder.keepalive(timeout=timedelta(seconds=-5))

    def test_interval_int_rejects_bool_subclass(self):
        """Test that bool is rejected for interval even though bool is int subclass."""
        builder = ClientBuilder("localhost:8080")
        with pytest.raises(TypeError, match="interval must be a timedelta"):
            builder.keepalive(interval=True)


class TestBuildChannelOptions:
    """Test ClientBuilder._build_channel_options() across all channel paths."""

    def test_sync_defaults_include_keepalive(self):
        """Test that sync build includes all keepalive defaults."""
        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=True))
        assert options["grpc.keepalive_time_ms"] == 45_000
        assert options["grpc.keepalive_timeout_ms"] == 10_000
        assert options["grpc.keepalive_permit_without_calls"] == 1
        assert options["grpc.http2.max_pings_without_data"] == 0

    def test_async_defaults_include_keepalive(self):
        """Test that async build includes all keepalive defaults."""
        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=False))
        assert options["grpc.keepalive_time_ms"] == 45_000
        assert options["grpc.keepalive_timeout_ms"] == 10_000
        assert options["grpc.keepalive_permit_without_calls"] == 1
        assert options["grpc.http2.max_pings_without_data"] == 0

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

    def test_keepalive_override_reaches_sync_options(self):
        """Test that keepalive() overrides reach sync channel options."""
        builder = ClientBuilder("localhost:8080")
        builder.keepalive(
            interval=timedelta(seconds=30),
            timeout=timedelta(seconds=5),
            permit_without_calls=False,
        )
        options = dict(builder._build_channel_options(sync=True))
        assert options["grpc.keepalive_time_ms"] == 30_000
        assert options["grpc.keepalive_timeout_ms"] == 5_000
        assert options["grpc.keepalive_permit_without_calls"] == 0

    def test_keepalive_override_reaches_async_options(self):
        """Test that keepalive() overrides reach async channel options."""
        builder = ClientBuilder("localhost:8080")
        builder.keepalive(
            interval=timedelta(seconds=30),
            timeout=timedelta(seconds=5),
            permit_without_calls=False,
        )
        options = dict(builder._build_channel_options(sync=False))
        assert options["grpc.keepalive_time_ms"] == 30_000
        assert options["grpc.keepalive_timeout_ms"] == 5_000
        assert options["grpc.keepalive_permit_without_calls"] == 0

    def test_max_pings_without_data_always_zero(self):
        """Test that max_pings_without_data is always 0 regardless of keepalive()."""
        builder = ClientBuilder("localhost:8080")
        builder.keepalive(interval=timedelta(seconds=60))
        options_sync = dict(builder._build_channel_options(sync=True))
        options_async = dict(builder._build_channel_options(sync=False))
        assert options_sync["grpc.http2.max_pings_without_data"] == 0
        assert options_async["grpc.http2.max_pings_without_data"] == 0

    def test_sync_option_count_with_defaults(self):
        """Test that sync build returns exactly 5 options (4 keepalive + SingleThreaded)."""
        builder = ClientBuilder("localhost:8080")
        options = builder._build_channel_options(sync=True)
        assert len(options) == 5

    def test_async_option_count_with_defaults(self):
        """Test that async build returns exactly 4 options (keepalive only)."""
        builder = ClientBuilder("localhost:8080")
        options = builder._build_channel_options(sync=False)
        assert len(options) == 4

    def test_keepalive_time_ms_default_value(self):
        """Test that keepalive_time_ms default is 45000."""
        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=False))
        assert options["grpc.keepalive_time_ms"] == 45_000

    def test_keepalive_timeout_ms_default_value(self):
        """Test that keepalive_timeout_ms default is 10000."""
        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=False))
        assert options["grpc.keepalive_timeout_ms"] == 10_000

    def test_keepalive_permit_without_calls_default_value(self):
        """Test that keepalive_permit_without_calls default is 1 (True)."""
        builder = ClientBuilder("localhost:8080")
        options = dict(builder._build_channel_options(sync=False))
        assert options["grpc.keepalive_permit_without_calls"] == 1

    def test_permit_without_calls_true_maps_to_1(self):
        """Test that permit_without_calls=True maps to gRPC integer 1."""
        builder = ClientBuilder("localhost:8080")
        builder.keepalive(permit_without_calls=True)
        options = dict(builder._build_channel_options(sync=False))
        assert options["grpc.keepalive_permit_without_calls"] == 1

    def test_permit_without_calls_false_maps_to_0(self):
        """Test that permit_without_calls=False maps to gRPC integer 0."""
        builder = ClientBuilder("localhost:8080")
        builder.keepalive(permit_without_calls=False)
        options = dict(builder._build_channel_options(sync=False))
        assert options["grpc.keepalive_permit_without_calls"] == 0


class TestKeepaliveDefaults:
    """Test that module-level keepalive defaults are correct."""

    def test_default_interval_is_45_seconds(self):
        """Test that the default keepalive interval is 45000 ms."""
        assert _DEFAULT_KEEPALIVE_INTERVAL_MS == 45_000

    def test_default_timeout_is_10_seconds(self):
        """Test that the default keepalive timeout is 10000 ms."""
        assert _DEFAULT_KEEPALIVE_TIMEOUT_MS == 10_000

    def test_default_permit_without_calls_is_true(self):
        """Test that keepalive pings without active RPCs are permitted by default."""
        assert _DEFAULT_KEEPALIVE_PERMIT_WITHOUT_CALLS is True

    def test_builder_initializes_with_defaults(self):
        """Test that ClientBuilder starts with the module-level defaults."""
        builder = ClientBuilder("localhost:8080")
        assert builder._keepalive_interval_ms == _DEFAULT_KEEPALIVE_INTERVAL_MS
        assert builder._keepalive_timeout_ms == _DEFAULT_KEEPALIVE_TIMEOUT_MS
        assert builder._keepalive_permit_without_calls == _DEFAULT_KEEPALIVE_PERMIT_WITHOUT_CALLS
