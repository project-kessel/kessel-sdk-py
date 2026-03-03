from kessel.inventory.v1beta2 import check_self_bulk_request_pb2 as _check_self_bulk_request_pb2
from kessel.inventory.v1beta2 import allowed_pb2 as _allowed_pb2
from buf.validate import validate_pb2 as _validate_pb2
from google.rpc import status_pb2 as _status_pb2
from kessel.inventory.v1beta2 import consistency_token_pb2 as _consistency_token_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CheckSelfBulkResponseItem(_message.Message):
    __slots__ = ("allowed",)
    ALLOWED_FIELD_NUMBER: _ClassVar[int]
    allowed: _allowed_pb2.Allowed
    def __init__(self, allowed: _Optional[_Union[_allowed_pb2.Allowed, str]] = ...) -> None: ...

class CheckSelfBulkResponsePair(_message.Message):
    __slots__ = ("request", "item", "error")
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    request: _check_self_bulk_request_pb2.CheckSelfBulkRequestItem
    item: CheckSelfBulkResponseItem
    error: _status_pb2.Status
    def __init__(self, request: _Optional[_Union[_check_self_bulk_request_pb2.CheckSelfBulkRequestItem, _Mapping]] = ..., item: _Optional[_Union[CheckSelfBulkResponseItem, _Mapping]] = ..., error: _Optional[_Union[_status_pb2.Status, _Mapping]] = ...) -> None: ...

class CheckSelfBulkResponse(_message.Message):
    __slots__ = ("pairs", "consistency_token")
    PAIRS_FIELD_NUMBER: _ClassVar[int]
    CONSISTENCY_TOKEN_FIELD_NUMBER: _ClassVar[int]
    pairs: _containers.RepeatedCompositeFieldContainer[CheckSelfBulkResponsePair]
    consistency_token: _consistency_token_pb2.ConsistencyToken
    def __init__(self, pairs: _Optional[_Iterable[_Union[CheckSelfBulkResponsePair, _Mapping]]] = ..., consistency_token: _Optional[_Union[_consistency_token_pb2.ConsistencyToken, _Mapping]] = ...) -> None: ...
