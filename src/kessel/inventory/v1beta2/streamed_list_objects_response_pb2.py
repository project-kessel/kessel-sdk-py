# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: kessel/inventory/v1beta2/streamed_list_objects_response.proto
# Protobuf Python Version: 6.31.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    6,
    31,
    1,
    '',
    'kessel/inventory/v1beta2/streamed_list_objects_response.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from kessel.inventory.v1beta2 import resource_reference_pb2 as kessel_dot_inventory_dot_v1beta2_dot_resource__reference__pb2
from kessel.inventory.v1beta2 import response_pagination_pb2 as kessel_dot_inventory_dot_v1beta2_dot_response__pagination__pb2
from kessel.inventory.v1beta2 import consistency_token_pb2 as kessel_dot_inventory_dot_v1beta2_dot_consistency__token__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n=kessel/inventory/v1beta2/streamed_list_objects_response.proto\x12\x18kessel.inventory.v1beta2\x1a\x31kessel/inventory/v1beta2/resource_reference.proto\x1a\x32kessel/inventory/v1beta2/response_pagination.proto\x1a\x30kessel/inventory/v1beta2/consistency_token.proto\"\x89\x02\n\x1bStreamedListObjectsResponse\x12\x43\n\x06object\x18\x01 \x01(\x0b\x32+.kessel.inventory.v1beta2.ResourceReferenceR\x06object\x12L\n\npagination\x18\x02 \x01(\x0b\x32,.kessel.inventory.v1beta2.ResponsePaginationR\npagination\x12W\n\x11\x63onsistency_token\x18\x03 \x01(\x0b\x32*.kessel.inventory.v1beta2.ConsistencyTokenR\x10\x63onsistencyTokenBr\n(org.project_kessel.api.inventory.v1beta2P\x01ZDgithub.com/project-kessel/inventory-api/api/kessel/inventory/v1beta2b\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'kessel.inventory.v1beta2.streamed_list_objects_response_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'\n(org.project_kessel.api.inventory.v1beta2P\001ZDgithub.com/project-kessel/inventory-api/api/kessel/inventory/v1beta2'
  _globals['_STREAMEDLISTOBJECTSRESPONSE']._serialized_start=245
  _globals['_STREAMEDLISTOBJECTSRESPONSE']._serialized_end=510
# @@protoc_insertion_point(module_scope)
