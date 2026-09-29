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

# Default HTTP/2 keepalive options for all gRPC channels.
# Keeps connections alive behind idle-timeout load balancers (e.g. 60 s
# Classic ELB / Istio gateway).  Callers can override individual keys
# via ClientBuilder.channel_options().
_DEFAULT_KEEPALIVE_OPTIONS = (
    ("grpc.keepalive_time_ms", 45_000),
    ("grpc.keepalive_timeout_ms", 10_000),
    ("grpc.keepalive_permit_without_calls", 1),
    ("grpc.http2.max_pings_without_data", 0),
)


class ClientBuilder:
    _stub_class = None

    def __init__(self, target: str):
        self._target = target
        self._call_credentials = None
        self._channel_credentials = None
        self._user_channel_options = None

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

    def channel_options(self, options: list[tuple[str, object]]) -> Self:
        """Set custom channel options that are merged with defaults.

        Caller-supplied keys override the built-in keepalive defaults.

        Args:
            options: List of ``(key, value)`` gRPC channel option tuples.

        Returns:
            ``self`` for method chaining.
        """
        self._user_channel_options = list(options)
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
        """Merge keepalive defaults, sync-only options, and caller overrides.

        Caller-supplied keys win when they collide with a default.
        """
        merged = dict(_DEFAULT_KEEPALIVE_OPTIONS)
        if sync:
            merged[ChannelOptions.SingleThreadedUnaryStream] = 1
        if self._user_channel_options:
            merged.update(self._user_channel_options)
        return list(merged.items())

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
