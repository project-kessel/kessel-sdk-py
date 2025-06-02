import grpc
from kessel.inventory import v1beta2
from kessel.inventory.v1beta2 import (
    streamed_list_objects_request_pb2,
    rbac,
    representation_type_pb2,
)


def run():
    stub = v1beta2.ClientBuilder.with_defaults_localhost(9000).build_inventory_stub()

    object_type = representation_type_pb2.RepresentationType(
        resource_type="host",
        reporter_type="hbi",
    )
    subject = rbac.principal_subject_for_user_id("1", "localhost")
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
