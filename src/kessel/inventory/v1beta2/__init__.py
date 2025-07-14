from collections.abc import Hashable

from kessel.grpc import BaseClientBuilder
from kessel.inventory.v1beta2.inventory_service_pb2_grpc import KesselInventoryServiceStub

from kessel.inventory.v1beta2.check_request_pb2 import CheckRequest
from kessel.inventory.v1beta2.check_response_pb2 import CheckResponse
from kessel.inventory.v1beta2.check_for_update_request_pb2 import CheckForUpdateRequest
from kessel.inventory.v1beta2.check_for_update_response_pb2 import CheckForUpdateResponse
from kessel.inventory.v1beta2.subject_reference_pb2 import SubjectReference
from kessel.inventory.v1beta2.resource_reference_pb2 import ResourceReference
from kessel.inventory.v1beta2.reporter_reference_pb2 import ReporterReference
from kessel.inventory.v1beta2.report_resource_request_pb2 import ReportResourceRequest
from kessel.inventory.v1beta2.report_resource_response_pb2 import ReportResourceResponse
from kessel.inventory.v1beta2.delete_resource_request_pb2 import DeleteResourceRequest
from kessel.inventory.v1beta2.delete_resource_response_pb2 import DeleteResourceResponse
from kessel.inventory.v1beta2.streamed_list_objects_request_pb2 import StreamedListObjectsRequest
from kessel.inventory.v1beta2.streamed_list_objects_response_pb2 import StreamedListObjectsResponse
from kessel.inventory.v1beta2.resource_representations_pb2 import ResourceRepresentations
from kessel.inventory.v1beta2.representation_metadata_pb2 import RepresentationMetadata
from kessel.inventory.v1beta2.representation_type_pb2 import RepresentationType
from kessel.inventory.v1beta2.request_pagination_pb2 import RequestPagination
from kessel.inventory.v1beta2.response_pagination_pb2 import ResponsePagination
from kessel.inventory.v1beta2.consistency_pb2 import Consistency
from kessel.inventory.v1beta2.consistency_token_pb2 import ConsistencyToken
from kessel.inventory.v1beta2.allowed_pb2 import Allowed
from kessel.inventory.v1beta2.write_visibility_pb2 import WriteVisibility


class ClientBuilder(BaseClientBuilder):
    """
    A builder for creating a Inventory gRPC client (sync or asyncio variants).

    Constructors "with defaults" provide a convenient way
    to set up the client with common, recommended defaults.
    """

    def build_inventory_stub(self) -> KesselInventoryServiceStub:
        return self.build_stub(KesselInventoryServiceStub)

    def build_or_get_inventory_stub(self, cacheKey: Hashable) -> KesselInventoryServiceStub:
        return self.build_or_get_existing_stub(cacheKey, KesselInventoryServiceStub)

__all__ = [
    'ClientBuilder',
    'KesselInventoryServiceStub',
    'CheckRequest',
    'CheckResponse', 
    'CheckForUpdateRequest',
    'CheckForUpdateResponse',
    'SubjectReference',
    'ResourceReference',
    'ReporterReference',
    'ReportResourceRequest',
    'ReportResourceResponse',
    'DeleteResourceRequest',
    'DeleteResourceResponse',
    'StreamedListObjectsRequest',
    'StreamedListObjectsResponse',
    'ResourceRepresentations',
    'RepresentationMetadata',
    'RepresentationType',
    'RequestPagination',
    'ResponsePagination',
    'Consistency',
    'ConsistencyToken',
    'Allowed',
    'WriteVisibility',
]
