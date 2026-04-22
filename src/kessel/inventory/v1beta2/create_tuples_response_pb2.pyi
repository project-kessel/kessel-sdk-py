from kessel.inventory.v1beta2 import consistency_token_pb2 as _consistency_token_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreateTuplesResponse(_message.Message):
    __slots__ = ("consistency_token",)
    CONSISTENCY_TOKEN_FIELD_NUMBER: _ClassVar[int]
    consistency_token: _consistency_token_pb2.ConsistencyToken
    def __init__(self, consistency_token: _Optional[_Union[_consistency_token_pb2.ConsistencyToken, _Mapping]] = ...) -> None: ...
