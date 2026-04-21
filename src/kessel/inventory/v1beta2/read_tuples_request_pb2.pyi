from buf.validate import validate_pb2 as _validate_pb2
from kessel.inventory.v1beta2 import relation_tuple_filter_pb2 as _relation_tuple_filter_pb2
from kessel.inventory.v1beta2 import request_pagination_pb2 as _request_pagination_pb2
from kessel.inventory.v1beta2 import consistency_pb2 as _consistency_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ReadTuplesRequest(_message.Message):
    __slots__ = ("filter", "pagination", "consistency")
    FILTER_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    CONSISTENCY_FIELD_NUMBER: _ClassVar[int]
    filter: _relation_tuple_filter_pb2.RelationTupleFilter
    pagination: _request_pagination_pb2.RequestPagination
    consistency: _consistency_pb2.Consistency
    def __init__(self, filter: _Optional[_Union[_relation_tuple_filter_pb2.RelationTupleFilter, _Mapping]] = ..., pagination: _Optional[_Union[_request_pagination_pb2.RequestPagination, _Mapping]] = ..., consistency: _Optional[_Union[_consistency_pb2.Consistency, _Mapping]] = ...) -> None: ...
