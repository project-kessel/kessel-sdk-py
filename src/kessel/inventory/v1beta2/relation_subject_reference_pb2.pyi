from buf.validate import validate_pb2 as _validate_pb2
from kessel.inventory.v1beta2 import relation_object_reference_pb2 as _relation_object_reference_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RelationSubjectReference(_message.Message):
    __slots__ = ("relation", "subject")
    RELATION_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    relation: str
    subject: _relation_object_reference_pb2.RelationObjectReference
    def __init__(self, relation: _Optional[str] = ..., subject: _Optional[_Union[_relation_object_reference_pb2.RelationObjectReference, _Mapping]] = ...) -> None: ...
