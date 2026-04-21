from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class AcquireLockResponse(_message.Message):
    __slots__ = ("lock_token",)
    LOCK_TOKEN_FIELD_NUMBER: _ClassVar[int]
    lock_token: str
    def __init__(self, lock_token: _Optional[str] = ...) -> None: ...
