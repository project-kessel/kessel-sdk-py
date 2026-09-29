from datetime import timedelta
from typing import Self, TYPE_CHECKING

if TYPE_CHECKING:
    from kessel.auth import OAuth2ClientCredentials

from grpc import (
    ChannelCredentials,
    CallCredentials,
    ssl_channel_credentials,
    composite_channel_credentials,
    insecure_channel,
    secure_channel,
)
from grpc.aio import (
    insecure_channel as insecure_channel_async,
    secure_channel as secure_channel_async,
)
from grpc.experimental import insecure_channel_credentials, ChannelOptions
from kessel.grpc import oauth2_call_credentials

# Default keepalive policy applied to every SDK-built channel.
# Keeps connections alive behind idle-timeout load balancers (e.g. 60 s
# Classic ELB / Istio gateway).  Callers can customise individual values
# via the typed ClientBuilder.keepalive() method.
_DEFAULT_KEEPALIVE_INTERVAL_MS = 45_000
_DEFAULT_KEEPALIVE_TIMEOUT_MS = 10_000
_DEFAULT_KEEPALIVE_PERMIT_WITHOUT_CALLS = True


class ClientBuilder:
    _stub_class = None

    def __init__(self, target: str):
        self._target = target
        self._call_credentials = None
        self._channel_credentials = None
        self._keepalive_interval_ms = _DEFAULT_KEEPALIVE_INTERVAL_MS
        self._keepalive_timeout_ms = _DEFAULT_KEEPALIVE_TIMEOUT_MS
        self._keepalive_permit_without_calls = _DEFAULT_KEEPALIVE_PERMIT_WITHOUT_CALLS

        if not self._target or type(self._target) is not str:
            raise TypeError("Invalid target type")

    def oauth2_client_authenticated(
        self,
        oauth2_client_credentials: "OAuth2ClientCredentials",
        channel_credentials: ChannelCredentials = None,
    ) -> Self:
        self._call_credentials = oauth2_call_credentials(oauth2_client_credentials)
        self._channel_credentials = channel_credentials
        self._validate_credentials()
        return self

    def authenticated(
        self,
        call_credentials: CallCredentials = None,
        channel_credentials: ChannelCredentials = None,
    ) -> Self:
        self._call_credentials = call_credentials
        self._channel_credentials = channel_credentials
        return self

    def unauthenticated(self, channel_credentials: ChannelCredentials = None) -> Self:
        self._call_credentials = None
        self._channel_credentials = channel_credentials
        return self

    def insecure(self) -> Self:
        self._call_credentials = None
        self._channel_credentials = insecure_channel_credentials()
        return self

    def keepalive(
        self,
        *,
        interval: timedelta | None = None,
        timeout: timedelta | None = None,
        permit_without_calls: bool | None = None,
    ) -> Self:
        """Customise the HTTP/2 keepalive policy for this channel.

        Keepalive is enabled by default on every SDK-built channel.
        Calling this method overrides only the supplied fields; omitted
        values retain their current effective defaults.  The method may
        be called more than once — each call updates only the fields it
        receives.

        Args:
            interval: Time of inactivity before sending a keepalive ping.
                Must be a positive ``timedelta``.  Default: 45 seconds.
            timeout: Time to wait for a keepalive ping ACK before closing
                the transport.  Must be a positive ``timedelta``.
                Default: 10 seconds.
            permit_without_calls: If ``True``, send keepalive pings even
                when there are no active RPCs on the channel.
                Default: ``True``.

        Returns:
            ``self`` for method chaining.

        Raises:
            TypeError: If *interval* or *timeout* is not a ``timedelta``,
                or *permit_without_calls* is not a ``bool``.
            ValueError: If *interval* or *timeout* is zero or negative.
        """
        if interval is not None:
            if not isinstance(interval, timedelta):
                raise TypeError("interval must be a timedelta, got " + type(interval).__name__)
            if interval <= timedelta(0):
                raise ValueError("interval must be positive")
            self._keepalive_interval_ms = int(interval / timedelta(milliseconds=1))
        if timeout is not None:
            if not isinstance(timeout, timedelta):
                raise TypeError("timeout must be a timedelta, got " + type(timeout).__name__)
            if timeout <= timedelta(0):
                raise ValueError("timeout must be positive")
            self._keepalive_timeout_ms = int(timeout / timedelta(milliseconds=1))
        if permit_without_calls is not None:
            if not isinstance(permit_without_calls, bool):
                raise TypeError(
                    "permit_without_calls must be a bool, got "
                    + type(permit_without_calls).__name__
                )
            self._keepalive_permit_without_calls = permit_without_calls
        return self

    def build(self):
        credentials = self._build_credentials()
        channel_options = self._build_channel_options(sync=True)

        if self._channel_credentials is insecure_channel_credentials():
            channel = insecure_channel(self._target, options=channel_options)
        else:
            channel = secure_channel(self._target, credentials=credentials, options=channel_options)

        return self._stub_class(channel), channel

    def build_async(self):
        credentials = self._build_credentials()
        channel_options = self._build_channel_options(sync=False)

        if self._channel_credentials is insecure_channel_credentials():
            channel = insecure_channel_async(self._target, options=channel_options)
        else:
            channel = secure_channel_async(
                self._target, credentials=credentials, options=channel_options
            )

        return self._stub_class(channel), channel

    def _build_channel_options(self, *, sync: bool) -> list[tuple]:
        """Build the gRPC channel options list from the current keepalive policy."""
        options = [
            ("grpc.keepalive_time_ms", self._keepalive_interval_ms),
            ("grpc.keepalive_timeout_ms", self._keepalive_timeout_ms),
            (
                "grpc.keepalive_permit_without_calls",
                1 if self._keepalive_permit_without_calls else 0,
            ),
            ("grpc.http2.max_pings_without_data", 0),
        ]
        if sync:
            options.append((ChannelOptions.SingleThreadedUnaryStream, 1))
        return options

    def _build_credentials(self):
        if self._channel_credentials is None:
            self._channel_credentials = ssl_channel_credentials()

        if self._call_credentials is not None:
            return composite_channel_credentials(self._channel_credentials, self._call_credentials)

        return self._channel_credentials

    def _validate_credentials(self):
        if (
            self._call_credentials is not None
            and self._channel_credentials is insecure_channel_credentials()
        ):
            raise ValueError(
                "Invalid credential configuration: can not authenticate with insecure channel"
            )


def client_builder_for_stub(stub_class) -> type[ClientBuilder]:
    class ConcreteClientBuilder(ClientBuilder):
        _stub_class = stub_class

    return ConcreteClientBuilder
