from google.protobuf import struct_pb2 as _struct_pb2
from kessel.inventory.v1beta2 import write_visibility_pb2 as _write_visibility_pb2
from buf.validate import validate_pb2 as _validate_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RemoveResourceRelationshipsRequest(_message.Message):
    __slots__ = ("inventory_id", "type", "reporter_type", "reporter_instance_id", "local_resource_id", "reporter", "common", "transaction_id", "write_visibility")
    INVENTORY_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    REPORTER_TYPE_FIELD_NUMBER: _ClassVar[int]
    REPORTER_INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    LOCAL_RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    REPORTER_FIELD_NUMBER: _ClassVar[int]
    COMMON_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    WRITE_VISIBILITY_FIELD_NUMBER: _ClassVar[int]
    inventory_id: str
    type: str
    reporter_type: str
    reporter_instance_id: str
    local_resource_id: str
    reporter: _struct_pb2.Struct
    common: _struct_pb2.Struct
    transaction_id: str
    write_visibility: _write_visibility_pb2.WriteVisibility
    def __init__(self, inventory_id: _Optional[str] = ..., type: _Optional[str] = ..., reporter_type: _Optional[str] = ..., reporter_instance_id: _Optional[str] = ..., local_resource_id: _Optional[str] = ..., reporter: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., common: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., transaction_id: _Optional[str] = ..., write_visibility: _Optional[_Union[_write_visibility_pb2.WriteVisibility, str]] = ...) -> None: ...
