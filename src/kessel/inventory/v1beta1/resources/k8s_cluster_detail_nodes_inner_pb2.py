# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: kessel/inventory/v1beta1/resources/k8s_cluster_detail_nodes_inner.proto
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
    'kessel/inventory/v1beta1/resources/k8s_cluster_detail_nodes_inner.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from buf.validate import validate_pb2 as buf_dot_validate_dot_validate__pb2
from kessel.inventory.v1beta1.resources import resource_label_pb2 as kessel_dot_inventory_dot_v1beta1_dot_resources_dot_resource__label__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\nGkessel/inventory/v1beta1/resources/k8s_cluster_detail_nodes_inner.proto\x12\"kessel.inventory.v1beta1.resources\x1a\x1b\x62uf/validate/validate.proto\x1a\x37kessel/inventory/v1beta1/resources/resource_label.proto\"\xd8\x01\n\x1aK8sClusterDetailNodesInner\x12\x1e\n\x04name\x18\x8b\xf5\xcd\x01 \x01(\tB\x07\xbaH\x04r\x02\x10\x01R\x04name\x12\x1b\n\x03\x63pu\x18\xa8\x83\x06 \x01(\tB\x07\xbaH\x04r\x02\x10\x01R\x03\x63pu\x12\"\n\x06memory\x18\x81\x86\xf5\x01 \x01(\tB\x07\xbaH\x04r\x02\x10\x01R\x06memory\x12Y\n\x06labels\x18\x83\xc0\xbe\x11 \x03(\x0b\x32\x31.kessel.inventory.v1beta1.resources.ResourceLabelB\x0b\xbaH\x08\x92\x01\x05\"\x03\xc8\x01\x01R\x06labelsB\xa7\x01\n2org.project_kessel.api.inventory.v1beta1.resourcesB\x1fK8sClusterDetailNodesInnerProtoP\x01ZNgithub.com/project-kessel/inventory-api/api/kessel/inventory/v1beta1/resourcesb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'kessel.inventory.v1beta1.resources.k8s_cluster_detail_nodes_inner_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'\n2org.project_kessel.api.inventory.v1beta1.resourcesB\037K8sClusterDetailNodesInnerProtoP\001ZNgithub.com/project-kessel/inventory-api/api/kessel/inventory/v1beta1/resources'
  _globals['_K8SCLUSTERDETAILNODESINNER'].fields_by_name['name']._loaded_options = None
  _globals['_K8SCLUSTERDETAILNODESINNER'].fields_by_name['name']._serialized_options = b'\272H\004r\002\020\001'
  _globals['_K8SCLUSTERDETAILNODESINNER'].fields_by_name['cpu']._loaded_options = None
  _globals['_K8SCLUSTERDETAILNODESINNER'].fields_by_name['cpu']._serialized_options = b'\272H\004r\002\020\001'
  _globals['_K8SCLUSTERDETAILNODESINNER'].fields_by_name['memory']._loaded_options = None
  _globals['_K8SCLUSTERDETAILNODESINNER'].fields_by_name['memory']._serialized_options = b'\272H\004r\002\020\001'
  _globals['_K8SCLUSTERDETAILNODESINNER'].fields_by_name['labels']._loaded_options = None
  _globals['_K8SCLUSTERDETAILNODESINNER'].fields_by_name['labels']._serialized_options = b'\272H\010\222\001\005\"\003\310\001\001'
  _globals['_K8SCLUSTERDETAILNODESINNER']._serialized_start=198
  _globals['_K8SCLUSTERDETAILNODESINNER']._serialized_end=414
# @@protoc_insertion_point(module_scope)
