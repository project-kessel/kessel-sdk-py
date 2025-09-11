from typing import Optional, AsyncIterator, Iterable

from kessel.inventory.v1beta2.representation_type_pb2 import RepresentationType
from kessel.inventory.v1beta2.resource_reference_pb2 import ResourceReference
from kessel.inventory.v1beta2.subject_reference_pb2 import SubjectReference
from kessel.inventory.v1beta2.reporter_reference_pb2 import ReporterReference
from kessel.inventory.v1beta2.streamed_list_objects_request_pb2 import StreamedListObjectsRequest
from kessel.inventory.v1beta2.streamed_list_objects_response_pb2 import StreamedListObjectsResponse
from kessel.inventory.v1beta2.inventory_service_pb2_grpc import KesselInventoryServiceStub

def workspace_type() -> RepresentationType:
    """
    Function to create a RepresentationType for workspace resources.
    Returns a protobuf RepresentationType configured for RBAC workspace objects.
    
    Returns:
        RepresentationType: A RepresentationType for workspace resources
    """
    return RepresentationType(resource_type="workspace", reporter_type="rbac")


def role_type() -> RepresentationType:
    """
    Function to create a RepresentationType for role resources.
    Returns a protobuf RepresentationType configured for RBAC role objects.

    Returns:
        RepresentationType: A RepresentationType for role resources
    """
    return RepresentationType(resource_type="role", reporter_type="rbac")


def principal_resource(id: str, domain: str) -> ResourceReference:
    """
    Creates a ResourceReference for a user principal based on user ID and domain.
    This function standardizes the creation of principal resources.
    
    Args:
        id: The user identifier
        domain: The domain or organization the user belongs to
    
    Returns:
        ResourceReference: A ResourceReference pointing to the user's principal resource
    """
    return ResourceReference(
        resource_type="principal",
        resource_id=f"{domain}/{id}",
        reporter=ReporterReference(type="rbac")
    )


def role_resource(resource_id: str) -> ResourceReference:
    """
    Function to create a ResourceReference for a role.
    Returns a protobuf ResourceReference configured for RBAC role resources.
    
    Args:
        resource_id: The role identifier
    
    Returns:
        ResourceReference: A ResourceReference for the role
    """
    return ResourceReference(
        resource_type="role",
        resource_id=resource_id,
        reporter=ReporterReference(type="rbac")
    )


def workspace_resource(resource_id: str) -> ResourceReference:
    """
    Function to create a ResourceReference for a workspace.
    Returns a protobuf ResourceReference configured for RBAC workspace resources.
    
    Args:
        resource_id: The workspace identifier
    
    Returns:
        ResourceReference: A ResourceReference for the workspace
    """
    return ResourceReference(
        resource_type="workspace",
        resource_id=resource_id,
        reporter=ReporterReference(type="rbac")
    )


def principal_subject(id: str, domain: str) -> SubjectReference:
    """
    Creates a SubjectReference for a user principal based on user ID and domain.
    This is a convenience function that wraps principal_resource to create a subject reference.
    
    Args:
        id: The user identifier
        domain: The domain or organization the user belongs to
    
    Returns:
        SubjectReference: A SubjectReference for the user's principal
    """
    return SubjectReference(
        resource=principal_resource(id, domain)
    )


def subject(resource_ref: ResourceReference, relation: Optional[str] = None) -> SubjectReference:
    """
    Creates a SubjectReference from a ResourceReference and an optional relation.
    This function allows you to easily create a subject reference.
    
    Args:
        resource_ref: The resource reference that identifies the subject
        relation: Optional relation that points to a set of subjects (e.g., "members", "owners")
    
    Returns:
        SubjectReference: A reference to a Subject or, if a relation is provided, a Subject Set.
    """
    if relation is not None:
        return SubjectReference(
            resource=resource_ref,
            relation=relation
        )
    else:
        return SubjectReference(
            resource=resource_ref
        )


def list_workspaces(
    subject: SubjectReference, 
    relation: str, 
    inventory: KesselInventoryServiceStub
) -> AsyncIterator[StreamedListObjectsResponse] | Iterable[StreamedListObjectsResponse]:
    """
    Lists all workspaces that a subject has a specific relation to.
    This function queries the inventory service to find workspaces based on the subject's permissions.
    
    Args:
        subject: The subject to check permissions for
        relation: The relationship type to check "member", "admin", "viewer")
        inventory: The inventory service client stub for making the request
    
    Returns:
        An iterator of workspace objects that the subject has the specified relation to
    """
    request = StreamedListObjectsRequest(
        object_type=workspace_type(),
        relation=relation,
        subject=subject
    )
    
    return inventory.StreamedListObjects(request)
