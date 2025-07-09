from typing import AsyncIterator, Iterable
from kessel.inventory.v1beta2 import streamed_list_objects_request_pb2
from kessel.inventory.v1beta2.inventory_service_pb2_grpc import KesselInventoryServiceStub
from kessel.inventory.v1beta2.reporter_reference_pb2 import ReporterReference
from kessel.inventory.v1beta2.representation_type_pb2 import RepresentationType
from kessel.inventory.v1beta2.resource_reference_pb2 import ResourceReference
from kessel.inventory.v1beta2.streamed_list_objects_response_pb2 import StreamedListObjectsResponse
from kessel.inventory.v1beta2.subject_reference_pb2 import SubjectReference


REPORTER = ReporterReference(type="rbac")
WORKSPACE = RepresentationType(resource_type="workspace", reporter_type="rbac")


def principal_resource_for_user_id(id: str, domain: str) -> ResourceReference:
    return ResourceReference(
        resource_type="principal", reporter=REPORTER, resource_id=f"{domain}/{id}"
    )


def principal_subject_for_user_id(id: str, domain: str) -> SubjectReference:
    return SubjectReference(resource=principal_resource_for_user_id(id, domain))


def list_workspaces(
    subject: SubjectReference, relation: str, inventory: KesselInventoryServiceStub
) -> AsyncIterator[StreamedListObjectsResponse] | Iterable[StreamedListObjectsResponse]:
    """List all workspaces."""
    request = streamed_list_objects_request_pb2.StreamedListObjectsRequest(
        object_type=WORKSPACE,
        relation=relation,
        subject=subject,
    )
    return inventory.StreamedListObjects(request)
