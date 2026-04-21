from kessel.inventory.v1beta2 import relationship_pb2 as _relationship_pb2
from kessel.inventory.v1beta2 import relation_fencing_check_pb2 as _relation_fencing_check_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreateTuplesRequest(_message.Message):
    __slots__ = ("upsert", "tuples", "fencing_check")
    UPSERT_FIELD_NUMBER: _ClassVar[int]
    TUPLES_FIELD_NUMBER: _ClassVar[int]
    FENCING_CHECK_FIELD_NUMBER: _ClassVar[int]
    upsert: bool
    tuples: _containers.RepeatedCompositeFieldContainer[_relationship_pb2.Relationship]
    fencing_check: _relation_fencing_check_pb2.RelationFencingCheck
    def __init__(self, upsert: bool = ..., tuples: _Optional[_Iterable[_Union[_relationship_pb2.Relationship, _Mapping]]] = ..., fencing_check: _Optional[_Union[_relation_fencing_check_pb2.RelationFencingCheck, _Mapping]] = ...) -> None: ...
