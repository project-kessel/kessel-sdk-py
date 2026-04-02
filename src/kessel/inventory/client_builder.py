"""
ClientBuilder for Connect-Python based Kessel SDK.

Provides a fluent builder API for creating authenticated Connect-Python clients
while maintaining backwards compatibility with the grpcio-based API.
"""
from typing import Self, TYPE_CHECKING

if TYPE_CHECKING:
    from kessel.auth import OAuth2ClientCredentials

from connectrpc.protocol import ProtocolType
from connectrpc.interceptor import (
    UnaryInterceptorSync,
    UnaryInterceptor,
)

from kessel.inventory.connect_wrapper import (
    StubWrapper,
    AsyncStubWrapper,
    ChannelWrapper,
    AsyncChannelWrapper,
)
from kessel.inventory.v1beta2.inventory_service_connect import (
    KesselInventoryServiceClientSync,
    KesselInventoryServiceClient,
)


class OAuth2Interceptor(UnaryInterceptorSync):
    """
    Synchronous interceptor that adds OAuth2 Bearer token to request headers.
    """

    def __init__(self, credentials: "OAuth2ClientCredentials"):
        """
        Initialize interceptor with OAuth2 credentials.

        Args:
            credentials: OAuth2ClientCredentials instance
        """
        self._credentials = credentials

    def intercept_unary_sync(self, next_handler, request, ctx):
        """Add OAuth2 bearer token to unary request."""
        # Get fresh token
        token_response = self._credentials.get_token()

        ctx.request_headers()["authorization"] = f"Bearer {token_response.access_token}"
        return next_handler(request, ctx)


class AsyncOAuth2Interceptor(UnaryInterceptor):
    """
    Asynchronous interceptor that adds OAuth2 Bearer token to request headers.
    """

    def __init__(self, credentials: "OAuth2ClientCredentials"):
        """
        Initialize interceptor with OAuth2 credentials.

        Args:
            credentials: OAuth2ClientCredentials instance
        """
        self._credentials = credentials

    async def intercept_unary(self, next_handler, request, ctx):
        """Add OAuth2 bearer token to async unary request."""
        # Get fresh token
        token_response = self._credentials.get_token() # TODO: Check if there is an async version of this

        # Add to headers
        ctx.request_headers()["authorization"] = f"Bearer {token_response.access_token}"

        return await next_handler(request, ctx)


class ClientBuilder:
    """
    Fluent builder for creating Connect-Python clients.

    Maintains API compatibility with grpcio-based ClientBuilder while using
    Connect-Python internally for pure Python implementation and faster builds.

    Example:
        # Insecure connection
        stub, channel = ClientBuilder("localhost:9000").insecure().build()

        # OAuth2 authenticated
        stub, channel = ClientBuilder("localhost:9000")
            .oauth2_client_authenticated(credentials)
            .build()

        # Async client
        stub, channel = ClientBuilder("localhost:9000").insecure().build_async()
    """

    def __init__(self, target: str):
        """
        Initialize ClientBuilder with target endpoint.

        Args:
            target: Server address (e.g., "localhost:9000")

        Raises:
            TypeError: If target is not a string
        """
        self._target = target
        self._oauth2_credentials = None
        self._insecure = False
        self._call_credentials = None
        self._channel_credentials = None

        if not self._target or type(self._target) is not str:
            raise TypeError("Invalid target type")

    def oauth2_client_authenticated(
        self,
        oauth2_client_credentials: "OAuth2ClientCredentials",
        channel_credentials=None,
    ) -> Self:
        """
        Configure OAuth2 client credentials authentication.

        Args:
            oauth2_client_credentials: OAuth2 credentials instance
            channel_credentials: Channel credentials (for TLS) - currently unused

        Returns:
            Self for method chaining
        """
        self._oauth2_credentials = oauth2_client_credentials
        self._channel_credentials = channel_credentials
        self._insecure = False
        return self

    def authenticated(self, call_credentials=None, channel_credentials=None) -> Self:
        """
        Configure generic authentication.

        Note: call_credentials are currently not supported with Connect-Python.
        Use oauth2_client_authenticated() instead.

        Args:
            call_credentials: Call credentials (not supported)
            channel_credentials: Channel credentials (for TLS)

        Returns:
            Self for method chaining
        """
        if call_credentials is not None:
            raise NotImplementedError(
                "Generic call_credentials are not supported with Connect-Python. "
                "Use oauth2_client_authenticated() for OAuth2 authentication."
            )
        self._call_credentials = call_credentials
        self._channel_credentials = channel_credentials
        return self

    def unauthenticated(self, channel_credentials=None) -> Self:
        """
        Configure unauthenticated connection.

        Args:
            channel_credentials: Channel credentials (for TLS) - currently unused

        Returns:
            Self for method chaining
        """
        self._call_credentials = None
        self._oauth2_credentials = None
        self._channel_credentials = channel_credentials
        return self

    def insecure(self) -> Self:
        """
        Configure insecure (HTTP) connection.

        Returns:
            Self for method chaining
        """
        self._insecure = True
        self._call_credentials = None
        self._oauth2_credentials = None
        self._channel_credentials = None
        return self

    def build(self):
        """
        Build synchronous client and channel.

        Returns:
            Tuple of (stub, channel) where:
                - stub: StubWrapper providing grpcio-compatible API
                - channel: ChannelWrapper providing context manager

        Example:
            stub, channel = ClientBuilder("localhost:9000").insecure().build()
            with channel:
                response = stub.Check(request)
        """
        # Determine address with protocol
        protocol_scheme = "http" if self._insecure else "https"
        address = f"{protocol_scheme}://{self._target}"

        # Build interceptors list
        interceptors = []
        if self._oauth2_credentials:
            interceptors.append(OAuth2Interceptor(self._oauth2_credentials))

        # Create Connect client using gRPC protocol
        # For non-TLS gRPC, configure HTTP/2 transport explicitly
        # See: https://connectrpc.com/docs/python/grpc-compatibility
        from pyqwest import SyncClient, SyncHTTPTransport, HTTPVersion
        http2_transport = SyncHTTPTransport(http_version=HTTPVersion.HTTP2)
        http_client = SyncClient(transport=http2_transport)

        connect_client = KesselInventoryServiceClientSync(
            address=address,
            protocol=ProtocolType.GRPC,  # Use gRPC protocol
            http_client=http_client,
            send_compression=None,  # Send uncompressed (server will indicate support via headers)
            interceptors=tuple(interceptors) if interceptors else (),
        )

        # Wrap to match grpcio API
        stub = StubWrapper(connect_client)
        channel = ChannelWrapper(connect_client)

        return stub, channel

    def build_async(self):
        """
        Build asynchronous client and channel.

        Returns:
            Tuple of (stub, channel) where:
                - stub: AsyncStubWrapper providing grpcio.aio-compatible API
                - channel: AsyncChannelWrapper providing async context manager

        Example:
            stub, channel = ClientBuilder("localhost:9000").insecure().build_async()
            async with channel:
                response = await stub.Check(request)
        """
        # Determine address with protocol
        protocol_scheme = "http" if self._insecure else "https"
        address = f"{protocol_scheme}://{self._target}"

        # Build interceptors list
        interceptors = []
        if self._oauth2_credentials:
            interceptors.append(AsyncOAuth2Interceptor(self._oauth2_credentials))

        # Create Connect async client using gRPC protocol
        # For non-TLS gRPC, configure HTTP/2 transport explicitly
        # See: https://connectrpc.com/docs/python/grpc-compatibility
        from pyqwest import Client, HTTPTransport, HTTPVersion
        http2_transport = HTTPTransport(http_version=HTTPVersion.HTTP2)
        http_client = Client(transport=http2_transport)

        connect_client = KesselInventoryServiceClient(
            address=address,
            protocol=ProtocolType.GRPC,  # Use gRPC protocol to talk to kratos-go
            http_client=http_client,
            send_compression=None,  # Send uncompressed (server will indicate support via headers)
            interceptors=tuple(interceptors) if interceptors else (),
        )

        # Wrap to match grpcio.aio API
        stub = AsyncStubWrapper(connect_client)
        channel = AsyncChannelWrapper(connect_client)

        return stub, channel
