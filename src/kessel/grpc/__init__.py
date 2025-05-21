from grpc import Channel
import grpc


def insecure(target: str) -> Channel:
    return grpc.insecure_channel(target, options=[("SingleThreadedUnaryStream", 1)])

class ChannelBuilder():
    _server_tls_credential: grpc.ServerCredentials | None
    _single_threaded_unary_stream: bool = True
    _asyncio: bool = False

    

    def build(self) -> Channel:
        