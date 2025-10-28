from kessel.inventory.v1beta2 import (
    # ClientBuilder,
    inventory_service_pb2_grpc,
    representation_type_pb2,
    resource_reference_pb2,
    subject_reference_pb2,
    streamed_list_objects_request_pb2,
)


def get_resources(
    client_stub: inventory_service_pb2_grpc.KesselInventoryServiceStub,
    object_type: representation_type_pb2.RepresentationType,
    relation: str,
    subject: subject_reference_pb2.SubjectReference,
    limit: int = 20,
    fetch_all=True
) -> Generator[
    resource_reference_pb2.ResourceReference, None, None
]:
    """
    Get a continuous stream of the object type this subject has this relation
    to.  Works around the inherent pagination and continuation token handling.

    Object type and subject are the PB2 representations, so your code can
    translate from your own internal representation.

    E.g.:

    >>> get_resources(
            Workspace('default').as_pb2(), 'member', this_user.as_pb2()
        )
    generator object (...)

    """
    continuation_token = None
    while (response := _get_resource_page(
        object_type, relation, subject, limit, continuation_token
    )) is not None:
        for data in response:
            yield data.object
        if not fetch_all:
            # We only want the first page
            break
        continuation_token = data.pagination.continuation_token
        if not continuation_token:
            # Could just make another request and then get told no more pages,
            # but it's neater this way...
            break



def _get_resource_page(
    client_stub: inventory_service_pb2_grpc.KesselInventoryServiceStub,
    object_type: representation_type_pb2.RepresentationType,
    relation: str,
    subject: subject_reference_pb2.SubjectReference,
    limit: int,
    continuation_token: Optional[str] = None
) -> streamed_list_objects_response_pb2.StreamedListObjectsResponse:
    """
    Get a single page, of at most limit size, from continuation_token (or
    start if None).
    """
    request = streamed_list_objects_request_pb2.StreamedListObjectsRequest(
        object_type=object_type,
        relation=relation,
        subject=subject,
        pagination=request_pagination_pb2.RequestPagination(
            limit=limit,
            continuation_token=continuation_token
        )
    )

    return client_stub.StreamedListObjects(request)
