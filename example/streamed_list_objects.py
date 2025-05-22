import grpc
from kessel import grpc as kessel_grpc
from kessel.inventory.v1beta2 import (
    inventory_service_pb2_grpc,
    streamed_list_objects_request_pb2,
    representation_type_pb2,
)
from kessel.rbac import v1beta2_resources


def run():
    channel = kessel_grpc.ChannelBuilder.with_defaults_localhost(9000).build()
    stub = inventory_service_pb2_grpc.KesselInventoryServiceStub(channel)

    object_type = representation_type_pb2.RepresentationType(
        resource_type="host",
        reporter_type="hbi",
    )
    subject = v1beta2_resources.principal_subject_for_user_id("1", "localhost")
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
