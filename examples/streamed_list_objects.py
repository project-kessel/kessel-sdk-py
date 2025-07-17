import grpc
from kessel.inventory import v1beta2
from kessel.inventory.v1beta2 import (
    RepresentationType,
    ReporterReference,
    ResourceReference,
    StreamedListObjectsRequest,
    SubjectReference,
)


def run():
    stub = v1beta2.KesselInventoryServiceStub(grpc.insecure_channel("localhost:9000"))

    object_type = RepresentationType(
        resource_type="host",
        reporter_type="hbi",
    )
    subject = SubjectReference(
        resource=ResourceReference(
            reporter=ReporterReference(type="rbac"), resource_id="1", resource_type="principal"
        )
    )
    request = StreamedListObjectsRequest(
        object_type=object_type,
        relation="view",
        subject=subject,
    )

    try:
        responses = stub.StreamedListObjects(request)
        print("Received streamed responses:")
        for response in responses:
            print(response)

    except grpc.RpcError as e:
        print("gRPC error occurred:")
        print(f"Code: {e.code()}")
        print(f"Details: {e.details()}")


if __name__ == "__main__":
    run()
