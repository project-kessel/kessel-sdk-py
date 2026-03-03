from kessel.inventory.v1beta2 import allowed_pb2 as _allowed_pb2
from kessel.inventory.v1beta2 import consistency_token_pb2 as _consistency_token_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CheckSelfResponse(_message.Message):
    __slots__ = ("allowed", "consistency_token")
    ALLOWED_FIELD_NUMBER: _ClassVar[int]
    CONSISTENCY_TOKEN_FIELD_NUMBER: _ClassVar[int]
    allowed: _allowed_pb2.Allowed
    consistency_token: _consistency_token_pb2.ConsistencyToken
    def __init__(self, allowed: _Optional[_Union[_allowed_pb2.Allowed, str]] = ..., consistency_token: _Optional[_Union[_consistency_token_pb2.ConsistencyToken, _Mapping]] = ...) -> None: ...
