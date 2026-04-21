from buf.validate import validate_pb2 as _validate_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class RelationFencingCheck(_message.Message):
    __slots__ = ("lock_id", "lock_token")
    LOCK_ID_FIELD_NUMBER: _ClassVar[int]
    LOCK_TOKEN_FIELD_NUMBER: _ClassVar[int]
    lock_id: str
    lock_token: str
    def __init__(self, lock_id: _Optional[str] = ..., lock_token: _Optional[str] = ...) -> None: ...
