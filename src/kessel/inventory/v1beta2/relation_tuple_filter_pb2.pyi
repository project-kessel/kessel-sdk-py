from kessel.inventory.v1beta2 import relation_subject_filter_pb2 as _relation_subject_filter_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RelationTupleFilter(_message.Message):
    __slots__ = ("resource_namespace", "resource_type", "resource_id", "relation", "subject_filter")
    RESOURCE_NAMESPACE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    RELATION_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_FILTER_FIELD_NUMBER: _ClassVar[int]
    resource_namespace: str
    resource_type: str
    resource_id: str
    relation: str
    subject_filter: _relation_subject_filter_pb2.RelationSubjectFilter
    def __init__(self, resource_namespace: _Optional[str] = ..., resource_type: _Optional[str] = ..., resource_id: _Optional[str] = ..., relation: _Optional[str] = ..., subject_filter: _Optional[_Union[_relation_subject_filter_pb2.RelationSubjectFilter, _Mapping]] = ...) -> None: ...
