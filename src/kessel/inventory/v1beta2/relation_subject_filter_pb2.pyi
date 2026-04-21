from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class RelationSubjectFilter(_message.Message):
    __slots__ = ("subject_namespace", "subject_type", "subject_id", "relation")
    SUBJECT_NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_TYPE_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    RELATION_FIELD_NUMBER: _ClassVar[int]
    subject_namespace: str
    subject_type: str
    subject_id: str
    relation: str
    def __init__(self, subject_namespace: _Optional[str] = ..., subject_type: _Optional[str] = ..., subject_id: _Optional[str] = ..., relation: _Optional[str] = ...) -> None: ...
