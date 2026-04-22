from kessel.inventory.v1beta2 import relationship_pb2 as _relationship_pb2
from kessel.inventory.v1beta2 import response_pagination_pb2 as _response_pagination_pb2
from kessel.inventory.v1beta2 import consistency_token_pb2 as _consistency_token_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ReadTuplesResponse(_message.Message):
    __slots__ = ("tuple", "pagination", "consistency_token")
    TUPLE_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    CONSISTENCY_TOKEN_FIELD_NUMBER: _ClassVar[int]
    tuple: _relationship_pb2.Relationship
    pagination: _response_pagination_pb2.ResponsePagination
    consistency_token: _consistency_token_pb2.ConsistencyToken
    def __init__(self, tuple: _Optional[_Union[_relationship_pb2.Relationship, _Mapping]] = ..., pagination: _Optional[_Union[_response_pagination_pb2.ResponsePagination, _Mapping]] = ..., consistency_token: _Optional[_Union[_consistency_token_pb2.ConsistencyToken, _Mapping]] = ...) -> None: ...
