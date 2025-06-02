from collections.abc import Callable, Hashable
from types import CoroutineType
from typing import Any, Self, TypeVar
import grpc

from kessel.inventory.v1beta2.inventory_service_pb2_grpc import KesselInventoryServiceStub

_global_channel_cache: dict[Hashable, grpc.aio.Channel | grpc.Channel] = {}
_global_stub_cache: dict[Hashable, Any] = {}


def close_cached_channels() -> None | CoroutineType:
    """Close all cached channels."""
    for channel in _global_channel_cache.values():
        if isinstance(channel, grpc.aio.Channel):
            return channel.close()
        else:
            channel.close()  # For synchronous channels
    _global_channel_cache.clear()


T = TypeVar("T")


class ClientBuilder:
    """
    A builder for creating a Inventory gRPC client (sync or asyncio variants).

    Constructors "with defaults" provide a convenient way
    to set up the client with common, recommended defaults.
    """

    _target: str
    # Only relevant if not using asyncio
    _single_threaded_unary_stream: bool = False
    _asyncio: bool = False
    _channel_credentials: grpc.ChannelCredentials | None = None
    _call_credentials: grpc.CallCredentials | None = None
    _keep_alive_time_ms: int | None = None
    _keep_alive_timeout_ms: int | None = None
    _max_pings_without_data: int | None = None
    _keep_alive_permit_without_calls: int | None = None

    def __init__(self, target: str):
        self._target = target

    @classmethod
    def with_defaults_insecure(cls, target: str) -> Self:
        builder = cls(target)
        builder._single_threaded_unary_stream = True
        builder._set_default_keep_alive()
        return builder

    @classmethod
    def with_defaults_localhost(
        cls, port: int, call_credentials: grpc.CallCredentials | None = None
    ) -> Self:
        builder = cls(f"localhost:{port}")
        builder._single_threaded_unary_stream = True
        builder._channel_credentials = grpc.local_channel_credentials()
        builder._call_credentials = call_credentials
        builder._set_default_keep_alive()
        return builder

    @classmethod
    def with_defaults(
        cls,
        target: str,
        call_credentials: grpc.CallCredentials,
        channel_credentials: grpc.ChannelCredentials = grpc.ssl_channel_credentials(),
    ) -> Self:
        builder = cls(target)
        builder._single_threaded_unary_stream = True
        builder._channel_credentials = channel_credentials
        builder._call_credentials = call_credentials
        builder._set_default_keep_alive()
        return builder

    def with_asyncio(self) -> Self:
        self._asyncio = True
        return self

    def with_keep_alive(
        self, time_ms: int, timeout_ms: int, max_pings: int, permit_without_calls: bool
    ) -> Self:
        self._keep_alive_time_ms = time_ms
        self._keep_alive_timeout_ms = timeout_ms
        self._max_pings_without_data = max_pings
        self._keep_alive_permit_without_calls = 1 if permit_without_calls else 0
        return self

    def build_channel(self) -> grpc.aio.Channel | grpc.Channel:
        chan_module = grpc.aio if self._asyncio else grpc
        options = []

        if not self._asyncio and self._single_threaded_unary_stream:
            options.append(("SingleThreadedUnaryStream", 1))

        _append_if_set("grpc.keepalive_time_ms", self._keep_alive_time_ms, options)
        _append_if_set("grpc.keepalive_timeout_ms", self._keep_alive_timeout_ms, options)
        _append_if_set("grpc.http2.max_pings_without_data", self._max_pings_without_data, options)
        _append_if_set(
            "grpc.keepalive_permit_without_calls", self._keep_alive_permit_without_calls, options
        )

        if not self._channel_credentials:
            return chan_module.insecure_channel(self._target, options)

        credentials = (
            grpc.composite_channel_credentials(
                self._channel_credentials,
                self._call_credentials,
            )
            if self._call_credentials
            else self._channel_credentials
        )

        return chan_module.secure_channel(
            self._target,
            credentials,
            options,
        )

    def build_channel_or_get_existing(self, cacheKey: Hashable) -> grpc.aio.Channel | grpc.Channel:
        if cacheKey in _global_channel_cache:
            return _global_channel_cache[cacheKey]

        channel = self.build_channel()
        _global_channel_cache[cacheKey] = channel
        return channel

    def build_stub(self, factory: Callable[[grpc.aio.Channel | grpc.Channel], T]) -> T:
        channel = self.build_channel()
        _global_channel_cache[self._target] = channel
        return factory(channel)

    def build_or_get_existing_stub(
        self, cacheKey: Hashable, factory: Callable[[grpc.aio.Channel | grpc.Channel], T]
    ) -> T:
        if cacheKey in _global_stub_cache:
            return _global_stub_cache[cacheKey]

        channel = self.build_channel_or_get_existing(cacheKey)
        stub = factory(channel)
        _global_stub_cache[cacheKey] = stub
        return stub

    def build_inventory_stub(self) -> KesselInventoryServiceStub:
        return self.build_stub(KesselInventoryServiceStub)

    def build_or_get_inventory_stub(self, cacheKey: Hashable) -> KesselInventoryServiceStub:
        return self.build_or_get_existing_stub(cacheKey, KesselInventoryServiceStub)

    def _set_default_keep_alive(self):
        self._keep_alive_time_ms = 10000
        self._keep_alive_timeout_ms = 5000
        self._max_pings_without_data = 12
        self._keep_alive_permit_without_calls = 1


def _append_if_set(option: str, value: int | None, options: list[tuple[str, int]]):
    if value is not None:
        options.append((option, value))
    return options
