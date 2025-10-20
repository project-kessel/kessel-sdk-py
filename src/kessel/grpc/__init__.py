import grpc
from typing import Callable, Any
from collections import namedtuple


_ClientCallDetails = namedtuple(
    "ClientCallDetails",
    ("method", "timeout", "metadata", "credentials", "wait_for_ready")
)

def oauth2_call_credentials(
    credentials: "kessel.auth.OAuth2ClientCredentials",
) -> grpc.CallCredentials:
    """
    Create gRPC call credentials from an OAuth2 client.

    Args:
        oauth2_client: An OAuth2ClientCredentials instance.

    Returns:
        grpc.CallCredentials: Call credentials that can be used with gRPC channels.
    """
    import google.auth.transport.grpc
    import google.auth.transport.requests
    from kessel.auth import GoogleOAuth2ClientCredentials

    auth_plugin = google.auth.transport.grpc.AuthMetadataPlugin(
        credentials=GoogleOAuth2ClientCredentials(credentials),
        request=google.auth.transport.requests.Request(),
    )

    return grpc.metadata_call_credentials(auth_plugin)


class AuthInterceptor(
    grpc.UnaryUnaryClientInterceptor,
    grpc.UnaryStreamClientInterceptor,
    grpc.StreamUnaryClientInterceptor,
    grpc.StreamStreamClientInterceptor,
):
    def __init__(self, credentials: "kessel.auth.OAuth2ClientCredentials"):
        self._credentials = credentials

    def _add_auth_metadata(self, client_call_details):
        """
        Add authentication metadata to the call details.
        """
        try:
            token_response = self._credentials.get_token()
            metadata = []
            if client_call_details.metadata is not None:
                metadata = list(client_call_details.metadata)
            metadata.append(("authorization", f"Bearer {token_response.access_token}"))

            return _ClientCallDetails(
                method=client_call_details.method,
                timeout=client_call_details.timeout,
                metadata=metadata,
                credentials=client_call_details.credentials,
                wait_for_ready=client_call_details.wait_for_ready,
            )
        except Exception as e:
            raise grpc.RpcError(f"Failed to acquire authentication token: {e}")

    def intercept_unary_unary(
        self,
        continuation: Callable,
        client_call_details: grpc.ClientCallDetails,
        request: Any,
    ) -> grpc.Call:
        new_details = self._add_auth_metadata(client_call_details)
        return continuation(new_details, request)

    def intercept_unary_stream(
        self,
        continuation: Callable,
        client_call_details: grpc.ClientCallDetails,
        request: Any,
    ) -> grpc.Call:
        new_details = self._add_auth_metadata(client_call_details)
        return continuation(new_details, request)

    def intercept_stream_unary(
        self,
        continuation: Callable,
        client_call_details: grpc.ClientCallDetails,
        request_iterator: Any,
    ) -> grpc.Call:
        new_details = self._add_auth_metadata(client_call_details)
        return continuation(new_details, request_iterator)

    def intercept_stream_stream(
        self,
        continuation: Callable,
        client_call_details: grpc.ClientCallDetails,
        request_iterator: Any,
    ) -> grpc.Call:
        new_details = self._add_auth_metadata(client_call_details)
        return continuation(new_details, request_iterator)


class AsyncAuthInterceptor(
    grpc.aio.UnaryUnaryClientInterceptor,
    grpc.aio.UnaryStreamClientInterceptor,
    grpc.aio.StreamUnaryClientInterceptor,
    grpc.aio.StreamStreamClientInterceptor,
):
    def __init__(self, credentials: "kessel.auth.OAuth2ClientCredentials"):
        self._credentials = credentials

    def _add_auth_metadata(self, client_call_details):
        """
        Add authentication metadata to the call details.
        """
        try:
            token_response = self._credentials.get_token()
            metadata = []
            if client_call_details.metadata is not None:
                metadata = list(client_call_details.metadata)
            metadata.append(("authorization", f"Bearer {token_response.access_token}"))

            return _ClientCallDetails(
                method=client_call_details.method,
                timeout=client_call_details.timeout,
                metadata=metadata,
                credentials=client_call_details.credentials,
                wait_for_ready=client_call_details.wait_for_ready,
            )
        except Exception as e:
            raise grpc.RpcError(f"Failed to acquire authentication token: {e}")

    async def intercept_unary_unary(
        self,
        continuation: Callable,
        client_call_details: grpc.aio.ClientCallDetails,
        request: Any,
    ) -> grpc.aio.UnaryUnaryCall:
        new_details = self._add_auth_metadata(client_call_details)
        return await continuation(new_details, request)

    async def intercept_unary_stream(
        self,
        continuation: Callable,
        client_call_details: grpc.aio.ClientCallDetails,
        request: Any,
    ) -> grpc.aio.UnaryStreamCall:
        new_details = self._add_auth_metadata(client_call_details)
        return await continuation(new_details, request)

    async def intercept_stream_unary(
        self,
        continuation: Callable,
        client_call_details: grpc.aio.ClientCallDetails,
        request_iterator: Any,
    ) -> grpc.aio.StreamUnaryCall:
        new_details = self._add_auth_metadata(client_call_details)
        return await continuation(new_details, request_iterator)

    async def intercept_stream_stream(
        self,
        continuation: Callable,
        client_call_details: grpc.aio.ClientCallDetails,
        request_iterator: Any,
    ) -> grpc.aio.StreamStreamCall:
        new_details = self._add_auth_metadata(client_call_details)
        return await continuation(new_details, request_iterator)
