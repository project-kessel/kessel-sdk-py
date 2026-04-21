from buf.validate import validate_pb2 as _validate_pb2
from kessel.inventory.v1beta2 import relation_object_type_pb2 as _relation_object_type_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RelationObjectReference(_message.Message):
    __slots__ = ("type", "id")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    type: _relation_object_type_pb2.RelationObjectType
    id: str
    def __init__(self, type: _Optional[_Union[_relation_object_type_pb2.RelationObjectType, _Mapping]] = ..., id: _Optional[str] = ...) -> None: ...
