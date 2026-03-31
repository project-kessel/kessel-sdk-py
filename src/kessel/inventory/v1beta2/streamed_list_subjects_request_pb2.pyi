from buf.validate import validate_pb2 as _validate_pb2
from kessel.inventory.v1beta2 import resource_reference_pb2 as _resource_reference_pb2
from kessel.inventory.v1beta2 import representation_type_pb2 as _representation_type_pb2
from kessel.inventory.v1beta2 import request_pagination_pb2 as _request_pagination_pb2
from kessel.inventory.v1beta2 import consistency_pb2 as _consistency_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StreamedListSubjectsRequest(_message.Message):
    __slots__ = ("resource", "relation", "subject_type", "subject_relation", "pagination", "consistency")
    RESOURCE_FIELD_NUMBER: _ClassVar[int]
    RELATION_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_TYPE_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_RELATION_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    CONSISTENCY_FIELD_NUMBER: _ClassVar[int]
    resource: _resource_reference_pb2.ResourceReference
    relation: str
    subject_type: _representation_type_pb2.RepresentationType
    subject_relation: str
    pagination: _request_pagination_pb2.RequestPagination
    consistency: _consistency_pb2.Consistency
    def __init__(self, resource: _Optional[_Union[_resource_reference_pb2.ResourceReference, _Mapping]] = ..., relation: _Optional[str] = ..., subject_type: _Optional[_Union[_representation_type_pb2.RepresentationType, _Mapping]] = ..., subject_relation: _Optional[str] = ..., pagination: _Optional[_Union[_request_pagination_pb2.RequestPagination, _Mapping]] = ..., consistency: _Optional[_Union[_consistency_pb2.Consistency, _Mapping]] = ...) -> None: ...
