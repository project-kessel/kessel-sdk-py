from typing import Self
from grpc import Channel
import grpc


class ChannelBuilder():
    # Only relevant if not using asyncio
    _target: str
    _single_threaded_unary_stream: bool = False
    _asyncio: bool = False
    _server_tls_credential: grpc.ServerCredentials | None
    _call_credential: grpc.CallCredentials | None

    @classmethod
    def with_defaults_insecure(cls, target: str, **kw) -> Self:
        builder = cls()
        builder._target = target
        builder._single_threaded_unary_stream = True
        return builder

    @classmethod
    def with_defaults(cls, target: str, **kw) -> Self:
        ...

    def with_asyncio(self) -> Self:
        self._asyncio = True
        return self

    def build(self) -> Channel:
        options = []
        if not self._asyncio and self._single_threaded_unary_stream:
            options.extend(("SingleThreadedUnaryStream", 1))
        return grpc.insecure_channel(self._target, options)
