from buf.validate import validate_pb2 as _validate_pb2
from kessel.inventory.v1beta2 import check_bulk_request_pb2 as _check_bulk_request_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CheckForUpdateBulkRequest(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[_check_bulk_request_pb2.CheckBulkRequestItem]
    def __init__(self, items: _Optional[_Iterable[_Union[_check_bulk_request_pb2.CheckBulkRequestItem, _Mapping]]] = ...) -> None: ...
