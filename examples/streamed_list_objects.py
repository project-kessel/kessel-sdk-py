import grpc

from kessel.inventory.v1beta2 import (
    inventory_service_pb2_grpc,
    representation_type_pb2,
    reporter_reference_pb2,
    resource_reference_pb2,
    streamed_list_objects_request_pb2,
    subject_reference_pb2,
)


def run():
    stub = inventory_service_pb2_grpc.KesselInventoryServiceStub(
        grpc.insecure_channel("localhost:9000")
    )

    object_type = representation_type_pb2.RepresentationType(
        resource_type="host",
        reporter_type="hbi",
    )
    subject = subject_reference_pb2.SubjectReference(
        resource=resource_reference_pb2.ResourceReference(
            reporter=reporter_reference_pb2.ReporterReference(type="rbac"),
            resource_id="1",
            resource_type="principal",
        )
    )
    request = streamed_list_objects_request_pb2.StreamedListObjectsRequest(
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
