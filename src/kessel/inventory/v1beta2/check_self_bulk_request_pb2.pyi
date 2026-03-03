from buf.validate import validate_pb2 as _validate_pb2
from kessel.inventory.v1beta2 import resource_reference_pb2 as _resource_reference_pb2
from kessel.inventory.v1beta2 import consistency_pb2 as _consistency_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CheckSelfBulkRequestItem(_message.Message):
    __slots__ = ("object", "relation")
    OBJECT_FIELD_NUMBER: _ClassVar[int]
    RELATION_FIELD_NUMBER: _ClassVar[int]
    object: _resource_reference_pb2.ResourceReference
    relation: str
    def __init__(self, object: _Optional[_Union[_resource_reference_pb2.ResourceReference, _Mapping]] = ..., relation: _Optional[str] = ...) -> None: ...

class CheckSelfBulkRequest(_message.Message):
    __slots__ = ("items", "consistency")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    CONSISTENCY_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[CheckSelfBulkRequestItem]
    consistency: _consistency_pb2.Consistency
    def __init__(self, items: _Optional[_Iterable[_Union[CheckSelfBulkRequestItem, _Mapping]]] = ..., consistency: _Optional[_Union[_consistency_pb2.Consistency, _Mapping]] = ...) -> None: ...
