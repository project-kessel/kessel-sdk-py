from buf.validate import validate_pb2 as _validate_pb2
from kessel.inventory.v1beta2 import relation_tuple_filter_pb2 as _relation_tuple_filter_pb2
from kessel.inventory.v1beta2 import relation_fencing_check_pb2 as _relation_fencing_check_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DeleteTuplesRequest(_message.Message):
    __slots__ = ("filter", "fencing_check")
    FILTER_FIELD_NUMBER: _ClassVar[int]
    FENCING_CHECK_FIELD_NUMBER: _ClassVar[int]
    filter: _relation_tuple_filter_pb2.RelationTupleFilter
    fencing_check: _relation_fencing_check_pb2.RelationFencingCheck
    def __init__(self, filter: _Optional[_Union[_relation_tuple_filter_pb2.RelationTupleFilter, _Mapping]] = ..., fencing_check: _Optional[_Union[_relation_fencing_check_pb2.RelationFencingCheck, _Mapping]] = ...) -> None: ...
